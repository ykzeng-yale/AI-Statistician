from __future__ import annotations

import hashlib
import json
import math
import tempfile
import zlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .fingerprint import stable_hash
from .model_backend import AnthropicGeneratorBackend, GeneratorBackend
from .scientific_sandbox import (
    ScientificEstimatorBinding,
    execute_scientific_sandbox,
)
from .theory_workspace import load_theory_workspace_document_rows
from .theory_semantic_gold_judge import run_theory_semantic_gold_judge


GOLD_EVALUATION_BOUNDARY = (
    "Evaluator-only gold runs after the AgentRuntime has terminated. Hidden "
    "harness source, expected values, and acceptance checks are never added to "
    "the blackboard, retrieval context, model prompt, or source-revision loop."
)
GoldHarnessRunner = Callable[..., Mapping[str, Any]]
GoldArtifactHarnessRunner = Callable[..., Mapping[str, Any]]
GoldTheorySemanticJudgeRunner = Callable[..., Mapping[str, Any]]


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
        "n_full_task_gold_configured": sum(
            str(task.get("scoring_scope", "component") or "component")
            == "full_task"
            for task in benchmark["active_tasks"]
        ),
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
            row["hidden_harness_execution_attempted"] is True for row in task_rows
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
    base = {
        "task_id": task_id,
        "level": str(task["level"]),
        "scoring_scope": str(
            task.get("scoring_scope", "component") or "component"
        ),
        "full_task_gold_configured": _full_task_gold_configured(task),
        "runtime_result_observed": runtime_result is not None,
        "runtime_research_eval_complete": (
            research_summary_row.get("research_eval_complete") is True
        ),
        "runtime_visible_question_hash": "",
        "accepted_algorithm_handoff_id": "",
        "accepted_algorithm_handoff_hash": "",
        "required_estimator_id": str(
            algorithm_evaluator.get("required_estimator_id", "") or ""
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
        "hidden_theory_execution_attempted": False,
        "hidden_theory_execution_passed": False,
        "hidden_theory_checks_passed": False,
        "hidden_theory_check_results": [],
        "hidden_theory_semantic_evaluation_configured": bool(
            theory_semantic_evaluator
        ),
        "hidden_theory_semantic_evaluator_hash": (
            stable_hash(theory_semantic_evaluator)
            if theory_semantic_evaluator
            else ""
        ),
        "hidden_theory_semantic_execution_attempted": False,
        "hidden_theory_semantic_judge_calibrated": False,
        "hidden_theory_semantic_calibration_case_count": 0,
        "hidden_theory_semantic_calibration_cases_correct": 0,
        "hidden_theory_semantic_claim_count": 0,
        "hidden_theory_semantic_candidate_status": "",
        "hidden_theory_semantic_passed": False,
        "hidden_theory_combined_passed": False,
        "hidden_empirical_evaluation_configured": bool(empirical_evaluator),
        "hidden_empirical_evaluator_source_hash": str(
            empirical_evaluator.get("harness_sha256", "") or ""
        ),
        "hidden_empirical_execution_attempted": False,
        "hidden_empirical_execution_passed": False,
        "hidden_empirical_checks_passed": False,
        "hidden_empirical_check_results": [],
        "source_replication_manifest_id": "",
        "source_replication_manifest_hash": "",
        "hidden_source_replication_evaluation_configured": bool(
            source_replication_evaluator
        ),
        "hidden_source_replication_evaluator_source_hash": str(
            source_replication_evaluator.get("harness_sha256", "") or ""
        ),
        "hidden_source_replication_execution_attempted": False,
        "hidden_source_replication_execution_passed": False,
        "hidden_source_replication_checks_passed": False,
        "hidden_source_replication_check_results": [],
        "source_replication_checkpoint_valid": False,
        "unresolved_gap_disclosure_present": False,
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
            hidden_theory_passed=False,
            hidden_algorithm_passed=False,
            hidden_empirical_passed=False,
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
            hidden_theory_passed=False,
            hidden_algorithm_passed=False,
            hidden_empirical_passed=False,
            runtime_result_observed=True,
        )
        return base

    artifacts = _runtime_artifacts(runtime_result)
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
            source_replication_gap_disclosure_present = (
                _source_replication_checkpoint_gap_disclosure_present(
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
            hidden_source_replication_passed = source_summary["passed"]
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
                }
            )
            base["failure_reasons"].extend(source_summary["errors"])
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
                try:
                    reference_documents, rubric, calibration_cases = (
                        _load_hidden_theory_semantic_authority(
                            theory_semantic_evaluator,
                            project_root=project_root,
                        )
                    )
                    if run_theory_semantic_judge is not None:
                        semantic_judgment = dict(
                            run_theory_semantic_judge(
                                task_id=task_id,
                                visible_question=runtime_question,
                                candidate_documents=authoritative_documents,
                                reference_documents=reference_documents,
                                rubric=rubric,
                                calibration_cases=calibration_cases,
                                model=str(theory_semantic_evaluator["model"]),
                                model_tier=str(
                                    theory_semantic_evaluator["model_tier"]
                                ),
                                max_tokens=int(
                                    theory_semantic_evaluator.get(
                                        "max_tokens", 6000
                                    )
                                    or 6000
                                ),
                            )
                        )
                    else:
                        semantic_provider = (
                            theory_semantic_judge_provider
                            or AnthropicGeneratorBackend(
                                timeout_s=float(
                                    theory_semantic_evaluator.get(
                                        "timeout_seconds", 120
                                    )
                                    or 120
                                )
                            )
                        )
                        semantic_judgment = run_theory_semantic_gold_judge(
                            provider=semantic_provider,
                            task_id=task_id,
                            visible_question=runtime_question,
                            candidate_documents=authoritative_documents,
                            reference_documents=reference_documents,
                            rubric=rubric,
                            calibration_cases=calibration_cases,
                            model=str(theory_semantic_evaluator["model"]),
                            model_tier=str(
                                theory_semantic_evaluator["model_tier"]
                            ),
                            max_tokens=int(
                                theory_semantic_evaluator.get(
                                    "max_tokens", 6000
                                )
                                or 6000
                            ),
                        )
                except Exception as exc:
                    base["failure_reasons"].append(
                        "hidden theory semantic evaluation failed closed: "
                        f"{type(exc).__name__}"
                    )
                else:
                    semantic_theory_passed = (
                        semantic_judgment.get("passed") is True
                    )
                    base.update(
                        {
                            "hidden_theory_semantic_execution_attempted": True,
                            "hidden_theory_semantic_result_hash": str(
                                semantic_judgment.get("judgment_hash", "") or ""
                            ),
                            "hidden_theory_semantic_judge_calibrated": (
                                semantic_judgment.get(
                                    "semantic_judge_calibrated"
                                )
                                is True
                            ),
                            "hidden_theory_semantic_calibration_case_count": int(
                                semantic_judgment.get(
                                    "n_calibration_cases", 0
                                )
                                or 0
                            ),
                            "hidden_theory_semantic_calibration_cases_correct": int(
                                semantic_judgment.get(
                                    "n_calibration_cases_correct", 0
                                )
                                or 0
                            ),
                            "hidden_theory_semantic_claim_count": int(
                                semantic_judgment.get("n_claims", 0) or 0
                            ),
                            "hidden_theory_semantic_candidate_status": str(
                                semantic_judgment.get("candidate_status", "")
                                or ""
                            ),
                            "hidden_theory_semantic_passed": (
                                semantic_theory_passed
                            ),
                        }
                    )
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
            runtime_research_eval_complete=(
                research_summary_row.get("research_eval_complete") is True
            ),
            hidden_theory_passed=hidden_theory_passed,
            hidden_algorithm_passed=True,
            hidden_empirical_passed=not empirical_evaluator,
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
        if source_replication_evaluator and not hidden_source_replication_passed:
            base["failure_reasons"].append(
                "hidden source-replication acceptance checks did not all pass"
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
                or research_summary_row.get("research_eval_complete") is True
            )
        )
        return base

    accepted_id, accepted_handoff, errors = _latest_accepted_algorithm_handoff(
        runtime_result,
        artifacts,
    )
    if errors:
        base["failure_reasons"].extend(errors)
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=(
                research_summary_row.get("research_eval_complete") is True
            ),
            hidden_theory_passed=hidden_theory_passed,
            hidden_algorithm_passed=False,
            hidden_empirical_passed=False,
            runtime_result_observed=True,
            source_replication_gap_disclosure_present=(
                source_replication_gap_disclosure_present
            ),
        )
        return base
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
        base["failure_reasons"].append(
            "accepted algorithm handoff does not contain exactly one required "
            f"estimator source: {estimator_id}"
        )
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=(
                research_summary_row.get("research_eval_complete") is True
            ),
            hidden_theory_passed=hidden_theory_passed,
            hidden_algorithm_passed=False,
            hidden_empirical_passed=False,
            runtime_result_observed=True,
            source_replication_gap_disclosure_present=(
                source_replication_gap_disclosure_present
            ),
        )
        return base
    source = source_rows[0]
    source_code = str(source.get("exact_source_code", "") or "")
    source_hash = str(source.get("exact_source_hash", "") or "")
    if not source_code or source_hash != stable_hash(source_code):
        base["failure_reasons"].append(
            "accepted estimator source is missing or its immutable hash is invalid"
        )
        base["dimension_status"] = _dimension_status(
            task,
            runtime_requirements=runtime_requirements,
            runtime_research_eval_complete=(
                research_summary_row.get("research_eval_complete") is True
            ),
            hidden_theory_passed=hidden_theory_passed,
            hidden_algorithm_passed=False,
            hidden_empirical_passed=False,
            runtime_result_observed=True,
            source_replication_gap_disclosure_present=(
                source_replication_gap_disclosure_present
            ),
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
            sandbox_dir=sandbox_root / task_id / "algorithm",
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
        runtime_research_eval_complete=(
            research_summary_row.get("research_eval_complete") is True
        ),
        hidden_theory_passed=hidden_theory_passed,
        hidden_algorithm_passed=hidden_algorithm_passed,
        hidden_empirical_passed=hidden_empirical_passed,
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
        and research_summary_row.get("research_eval_complete") is True
    )
    return base


def _dimension_status(
    task: Mapping[str, Any],
    *,
    runtime_requirements: Mapping[str, Any],
    runtime_research_eval_complete: bool,
    hidden_theory_passed: bool,
    hidden_algorithm_passed: bool,
    hidden_empirical_passed: bool,
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
        "formal": False,
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
                (dimension == "theory" and hidden_theory_passed)
                or (
                    dimension == "source_replication"
                    and hidden_source_replication_passed
                )
                or (dimension == "scientific_code" and hidden_algorithm_passed)
                or (dimension == "empirical" and hidden_empirical_passed)
            ),
            "evidence_authority": {
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
                "unresolved_gaps": (
                    "source_replication_checkpoint"
                    if source_replication_gap_disclosure_present
                    else "runtime_critic_disclosure"
                ),
            }.get(dimension, "not_configured"),
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
    rows = load_theory_workspace_document_rows(theory_packet)
    candidate["authoritative_theory_documents"] = rows
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


def _load_hidden_theory_semantic_authority(
    evaluator: Mapping[str, Any],
    *,
    project_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
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
    calibration_cases = calibration_payload.get("cases", [])
    if not isinstance(calibration_cases, list):
        raise ValueError("hidden theory semantic calibration cases are invalid")
    hydrated_cases: list[dict[str, Any]] = []
    for row in calibration_cases:
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
                    "hidden theory semantic calibration document hash mismatch"
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
    return reference_documents, rubric, hydrated_cases


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
    return not any(
        str(intent.get(dimension, "not_applicable")) == "required"
        for dimension in ("formal", "novelty")
    )


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
    return {"passed": passed}


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
        return str(artifact_id), artifact, []
    return "", {}, ["no runtime-generated source replication manifest was observed"]


def _source_replication_checkpoint_gap_disclosure_present(
    artifacts: Mapping[str, Any],
    *,
    question_id: str,
    source_manifest: Mapping[str, Any],
    task_intent: Any,
) -> bool:
    """Verify one model-authored report/gap checkpoint bound to the source run."""

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
            return False
        try:
            document_rows = load_theory_workspace_document_rows(workspace_evidence)
        except (OSError, UnicodeError, ValueError):
            return False
        return any(
            row.get("path") == report.get("relative_path")
            and row.get("sha256") == report.get("sha256")
            and str(row.get("content", "") or "").strip()
            for row in document_rows
        )
    return False


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
) -> Mapping[str, Any]:
    candidate_json = json.dumps(
        candidate_artifact,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    compressed_candidate = zlib.compress(candidate_json.encode("utf-8"), level=9)
    executable_code = (
        "import json as _gold_json\n"
        + "import zlib as _gold_zlib\n"
        + harness_code.rstrip()
        + "\n\n_gold_candidate = _gold_json.loads(_gold_zlib.decompress("
        + repr(compressed_candidate)
        + ").decode('utf-8'))\n"
        + "def run_sandbox(seed, replicates):\n"
        + "    return evaluate_artifact(\n"
        + "        _gold_candidate, seed=seed, replicates=replicates\n"
        + "    )\n"
    )
    execution = execute_scientific_sandbox(
        sandbox_dir=sandbox_dir,
        artifact_id=artifact_id,
        language="python",
        code=executable_code,
        dependencies=harness_dependencies,
        seed=seed,
        replicates=replicates,
        timeout_s=timeout_s,
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
        scoring_scope = str(
            task.get("scoring_scope", "component") or "component"
        )
        if scoring_scope not in {"component", "full_task"}:
            errors.append(
                f"active task {index} scoring_scope must be component or full_task"
            )
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
        algorithm_evaluator = task.get("hidden_algorithm_evaluator", {})
        algorithm_required = str(
            intent.get("scientific_code", "not_applicable")
            if isinstance(intent, Mapping)
            else "not_applicable"
        ) == "required"
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
                )
            )
        elif algorithm_required:
            errors.append(
                f"active task {index} hidden_algorithm_evaluator must be an object"
            )
        algorithm_estimator_id = str(
            algorithm_evaluator.get("required_estimator_id", "") or ""
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
                )
            )
            if require_estimator and str(
                evaluator.get("required_estimator_id", "") or ""
            ) != algorithm_estimator_id:
                errors.append(
                    f"active task {index} empirical evaluator estimator identity "
                    "must match the algorithm evaluator"
                )
        semantic_evaluator = task.get("hidden_theory_semantic_evaluator")
        if semantic_evaluator is not None:
            if not isinstance(semantic_evaluator, Mapping) or not semantic_evaluator:
                errors.append(
                    f"active task {index} hidden_theory_semantic_evaluator "
                    "must be a nonempty object"
                )
            else:
                errors.extend(
                    _hidden_theory_semantic_evaluator_validation_errors(
                        semantic_evaluator,
                        task_index=index,
                        project_root=project_root,
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
) -> list[str]:
    label = f"active task {task_index} hidden theory semantic evaluator"
    errors: list[str] = []
    if not (
        evaluator.get("provider") == "anthropic"
        and evaluator.get("model_tier") == "haiku"
        and evaluator.get("model") == "claude-haiku-4-5-20251001"
        and evaluator.get("automatic_tier_escalation_allowed") is False
    ):
        errors.append(f"{label} must use exact Haiku without escalation")
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
    for name, path_field, hash_field in (
        ("rubric", "rubric_path", "rubric_sha256"),
        (
            "calibration cases",
            "calibration_cases_path",
            "calibration_cases_sha256",
        ),
    ):
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
    calibration = authorities.get("calibration cases", {}).get("cases", [])
    if not isinstance(calibration, list) or not calibration:
        errors.append(f"{label} calibration cases are missing")
        calibration = []
    case_ids: list[str] = []
    expected_statuses: set[str] = set()
    for case_index, row in enumerate(calibration):
        if not isinstance(row, Mapping):
            errors.append(f"{label} calibration case {case_index} is invalid")
            continue
        case_id = str(row.get("case_id", "") or "")
        expected = str(row.get("expected_status", "") or "")
        case_ids.append(case_id)
        expected_statuses.add(expected)
        if not case_id or expected not in {"PASS", "FAIL", "INCONCLUSIVE"}:
            errors.append(
                f"{label} calibration case {case_index} identity or expectation is invalid"
            )
        if not isinstance(row.get("documents"), list) or not row.get("documents"):
            errors.append(f"{label} calibration case {case_index} has no documents")
            continue
        for document_index, document in enumerate(row.get("documents", []) or []):
            if not isinstance(document, Mapping):
                errors.append(
                    f"{label} calibration case {case_index} document "
                    f"{document_index} is invalid"
                )
                continue
            source_path_value = str(document.get("source_path", "") or "")
            if not source_path_value:
                if not str(document.get("content", "") or "").strip():
                    errors.append(
                        f"{label} calibration case {case_index} document "
                        f"{document_index} has no content"
                    )
                continue
            source_path = _project_path(
                source_path_value,
                project_root=project_root,
            )
            if not source_path.is_file():
                errors.append(
                    f"{label} calibration case {case_index} document "
                    f"{document_index} is missing"
                )
            elif _file_sha256(source_path) != str(
                document.get("sha256", "") or ""
            ):
                errors.append(
                    f"{label} calibration case {case_index} document "
                    f"{document_index} hash mismatch"
                )
    if len(set(case_ids)) != len(case_ids):
        errors.append(f"{label} calibration case identities repeat")
    if not {"PASS", "FAIL"} <= expected_statuses:
        errors.append(f"{label} calibration must contain both PASS and FAIL cases")
    return errors


def _hidden_evaluator_validation_errors(
    evaluator: Mapping[str, Any],
    *,
    task_index: int,
    label: str,
    project_root: Path,
    require_estimator: bool,
) -> list[str]:
    errors: list[str] = []
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
    for check_index, check in enumerate(checks):
        if not isinstance(check, Mapping):
            errors.append(
                f"active task {task_index} {label} check {check_index} "
                "must be an object"
            )
            continue
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
    return errors


def _project_path(value: str, *, project_root: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
