from __future__ import annotations

import json
from pathlib import Path

from ai_statistician.cli import main
from ai_statistician.source_theorem_exact_semantic_definition_lean_environment_repair_executor import (
    run_source_theorem_exact_semantic_definition_lean_environment_repair_executor,
)


def _write_environment_task(path: Path, *, project: Path, candidate: Path) -> None:
    row = {
        "schema_version": 1,
        "artifact_kind": "SourceTheoremExactSemanticDefinitionLeanEnvironmentRepairTask",
        "environment_repair_task_id": "lean-env-repair:orderStat",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "target_ids": ["split_conformal_coverage"],
        "placeholder_symbol": "orderStat",
        "candidate_source_file": str(candidate),
        "definition_only_candidate_artifact_path": str(candidate),
        "candidate_lean_project_hint": str(project),
        "source_execution_status": (
            "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING"
        ),
        "authoring_trigger": (
            "EXACT_SEMANTIC_DEFINITION_AUTHORING_REPAIR_REQUIRED"
        ),
        "authoring_mode": "repair_failed_exact_semantic_definition_candidate",
        "source_lean_repair_action": "author_exact_definition",
        "source_repair_strategy": "author_reviewed_definition_from_contract",
        "candidate_repair_feedback": {
            "failure_classification": "lean_import_environment_missing",
        },
        "candidate_definition_request": {
            "semantic_intent": "review exact order statistic definition"
        },
        "runtime_queue_status": "PENDING_LEAN_DEPENDENCY_ENVIRONMENT_REPAIR",
        "failure_classification": "lean_dependency_fetch_failed",
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
    }
    path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")


def test_lean_environment_repair_executor_detects_missing_manifest(
    tmp_path: Path,
) -> None:
    project = tmp_path / "LeanProject"
    candidate = project / "StatInference" / "Bootstrap.lean"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("-- source\n", encoding="utf-8")
    (project / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    (project / "lean-toolchain").write_text("leanprover/lean4:v4.30.0-rc2\n", encoding="utf-8")
    tasks = tmp_path / "environment_tasks.jsonl"
    _write_environment_task(tasks, project=project, candidate=candidate)

    manifest = run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
        out_dir=tmp_path / "out",
        environment_tasks_jsonl=tasks,
    )

    assert manifest["n_results"] == 1
    assert manifest["n_dependency_fetch_required"] == 1
    assert manifest["n_ready_to_rerun_lean_repair"] == 0
    results = [
        json.loads(line)
        for line in Path(manifest["environment_repair_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["environment_repair_status"] == (
        "LAKE_MANIFEST_MISSING_DEPENDENCY_UPDATE_REQUIRED"
    )
    assert results[0]["target_ids"] == ["split_conformal_coverage"]
    assert results[0]["definition_only_candidate_artifact_path"] == str(candidate)
    assert results[0]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING"
    )
    assert results[0]["authoring_mode"] == (
        "repair_failed_exact_semantic_definition_candidate"
    )
    assert results[0]["candidate_repair_feedback"]["failure_classification"] == (
        "lean_import_environment_missing"
    )
    assert results[0]["candidate_definition_request"]["placeholder_symbol"] == (
        "orderStat"
    )
    assert results[0]["candidate_definition_request"]["target_ids"] == [
        "split_conformal_coverage"
    ]
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["target_ids"] == ["split_conformal_coverage"]
    assert learning_rows[0]["input_summary"]["target_ids"] == [
        "split_conformal_coverage"
    ]
    assert results[0]["recommended_commands"][:2] == [
        "lake update",
        "lake exe cache get",
    ]
    assert results[0]["source_theorem_kernel_verified"] is False
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["input_summary"]["recommended_commands"][:2] == [
        "lake update",
        "lake exe cache get",
    ]
    assert learning_rows[0]["authoring_mode"] == (
        "repair_failed_exact_semantic_definition_candidate"
    )
    assert learning_rows[0]["environment_repair_status"] == (
        "LAKE_MANIFEST_MISSING_DEPENDENCY_UPDATE_REQUIRED"
    )
    assert learning_rows[0]["candidate_source_file"] == str(candidate)
    assert learning_rows[0]["definition_only_candidate_artifact_path"] == str(
        candidate
    )
    assert learning_rows[0]["input_summary"]["source_execution_status"] == (
        "TYPECHECKED_EXACT_DEFINITION_CANDIDATE_LEAN_IMPORT_ENVIRONMENT_MISSING"
    )
    assert learning_rows[0]["candidate_repair_feedback"][
        "failure_classification"
    ] == "lean_import_environment_missing"
    assert learning_rows[0]["candidate_definition_request"]["placeholder_symbol"] == (
        "orderStat"
    )
    assert learning_rows[0]["input_summary"]["candidate_definition_request"][
        "placeholder_symbol"
    ] == "orderStat"
    assert "prepare Lake dependencies/cache" in learning_rows[0]["input_summary"][
        "recommended_next_action"
    ]


def test_lean_environment_repair_executor_detects_ready_project(
    tmp_path: Path,
) -> None:
    project = tmp_path / "LeanProject"
    candidate = project / "StatInference" / "Bootstrap.lean"
    mathlib = project / ".lake" / "packages" / "mathlib"
    candidate.parent.mkdir(parents=True)
    mathlib.mkdir(parents=True)
    candidate.write_text("-- source\n", encoding="utf-8")
    (project / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    (project / "lean-toolchain").write_text("leanprover/lean4:v4.30.0-rc2\n", encoding="utf-8")
    (project / "lake-manifest.json").write_text("{}", encoding="utf-8")
    tasks = tmp_path / "environment_tasks.jsonl"
    _write_environment_task(tasks, project=project, candidate=candidate)

    manifest = run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
        out_dir=tmp_path / "out",
        environment_tasks_jsonl=tasks,
    )

    assert manifest["n_dependency_fetch_required"] == 0
    assert manifest["n_ready_to_rerun_lean_repair"] == 1
    results = [
        json.loads(line)
        for line in Path(manifest["environment_repair_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["environment_repair_status"] == (
        "DEPENDENCY_ENVIRONMENT_READY_TO_RERUN_LEAN_REPAIR"
    )
    assert results[0]["ready_to_rerun_lean_repair"] is True
    assert results[0]["proof_evidence_status"] == (
        "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_REPAIR_EXECUTION_NOT_PROOF_EVIDENCE"
    )


def test_lean_environment_repair_executor_keeps_local_library_build_unresolved(
    tmp_path: Path,
) -> None:
    project = tmp_path / "LeanProject"
    candidate = project / "StatInference" / "Bootstrap.lean"
    mathlib = project / ".lake" / "packages" / "mathlib"
    candidate.parent.mkdir(parents=True)
    mathlib.mkdir(parents=True)
    candidate.write_text("-- source\n", encoding="utf-8")
    (project / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    (project / "lean-toolchain").write_text("leanprover/lean4:v4.31.0\n", encoding="utf-8")
    (project / "lake-manifest.json").write_text("{}", encoding="utf-8")
    tasks = tmp_path / "environment_tasks.jsonl"
    _write_environment_task(tasks, project=project, candidate=candidate)
    row = json.loads(tasks.read_text(encoding="utf-8"))
    row["failure_classification"] = "lean_local_library_build_unresolved"
    tasks.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
        out_dir=tmp_path / "out",
        environment_tasks_jsonl=tasks,
    )

    assert manifest["n_dependency_fetch_required"] == 0
    assert manifest["n_ready_to_rerun_lean_repair"] == 0
    results = [
        json.loads(line)
        for line in Path(manifest["environment_repair_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["environment_repair_status"] == (
        "LOCAL_LIBRARY_BUILD_OR_IMPORT_UNRESOLVED"
    )
    assert results[0]["ready_to_rerun_lean_repair"] is False
    assert "dependency fetch is not the current blocker" in results[0][
        "recommended_next_action"
    ]


def test_lean_environment_repair_executor_detects_unavailable_import_prefix(
    tmp_path: Path,
) -> None:
    project = tmp_path / "LeanProject"
    candidate = project / "StatInference" / "Bootstrap.lean"
    mathlib = project / ".lake" / "packages" / "mathlib"
    candidate.parent.mkdir(parents=True)
    mathlib.mkdir(parents=True)
    candidate.write_text("import StatInference.Missing\n", encoding="utf-8")
    (project / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    (project / "lean-toolchain").write_text("leanprover/lean4:v4.31.0\n", encoding="utf-8")
    (project / "lake-manifest.json").write_text("{}", encoding="utf-8")
    tasks = tmp_path / "environment_tasks.jsonl"
    _write_environment_task(tasks, project=project, candidate=candidate)
    row = json.loads(tasks.read_text(encoding="utf-8"))
    row["failure_classification"] = "lean_import_environment_missing"
    row["local_lean_diagnostics"] = [
        f"{candidate}:1:0: error: unknown module prefix 'StatInference'",
        "No directory 'StatInference' or file 'StatInference.olean' in the search path entries:",
    ]
    tasks.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
        out_dir=tmp_path / "out",
        environment_tasks_jsonl=tasks,
    )

    assert manifest["n_dependency_fetch_required"] == 0
    assert manifest["n_import_prefix_unavailable"] == 1
    results = [
        json.loads(line)
        for line in Path(manifest["environment_repair_results_jsonl"]).read_text().splitlines()
    ]
    assert results[0]["environment_repair_status"] == (
        "LEAN_IMPORT_PREFIX_UNAVAILABLE_IN_PROJECT"
    )
    assert results[0]["unavailable_module_prefix"] == "StatInference"
    assert results[0]["ready_to_rerun_lean_repair"] is False
    assert results[0]["recommended_commands"] == [f"lake env lean {candidate}"]
    assert "Lake project/source root" in results[0]["recommended_next_action"]
    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["unavailable_module_prefix"] == "StatInference"
    assert learning_rows[0]["input_summary"]["unavailable_module_prefix"] == (
        "StatInference"
    )


def test_lean_environment_repair_executor_resolves_repair_manifest(
    tmp_path: Path,
) -> None:
    project = tmp_path / "LeanProject"
    candidate = project / "StatInference" / "Bootstrap.lean"
    candidate.parent.mkdir(parents=True)
    tasks = tmp_path / "environment_tasks.jsonl"
    repair_manifest = tmp_path / "repair_manifest.json"
    _write_environment_task(tasks, project=project, candidate=candidate)
    repair_manifest.write_text(
        json.dumps({"lean_environment_repair_tasks_jsonl": str(tasks)}),
        encoding="utf-8",
    )

    manifest = run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
        out_dir=tmp_path / "out",
        repair_executor_manifest=repair_manifest,
    )

    assert manifest["source_environment_tasks_jsonl"] == str(tasks)
    assert manifest["n_results"] == 1


def test_lean_environment_repair_executor_cli(tmp_path: Path) -> None:
    project = tmp_path / "LeanProject"
    candidate = project / "StatInference" / "Bootstrap.lean"
    candidate.parent.mkdir(parents=True)
    tasks = tmp_path / "environment_tasks.jsonl"
    out_dir = tmp_path / "out"
    _write_environment_task(tasks, project=project, candidate=candidate)

    rc = main(
        [
            "source-theorem-exact-semantic-definition-lean-environment-repair-executor",
            "--environment-tasks-jsonl",
            str(tasks),
            "--out",
            str(out_dir),
        ]
    )

    assert rc == 0
    manifest_path = (
        out_dir
        / "source_theorem_exact_semantic_definition_lean_environment_repair_executor_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["n_results"] == 1
    assert Path(manifest["runtime_learning_rows_jsonl"]).exists()
