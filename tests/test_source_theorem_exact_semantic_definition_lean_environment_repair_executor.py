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


def test_lean_environment_repair_executor_preserves_nested_anchor_bindings(
    tmp_path: Path,
) -> None:
    project = tmp_path / "LeanProject"
    candidate = project / "StatInference" / "Conformal.lean"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("-- source\n", encoding="utf-8")
    (project / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    (project / "lean-toolchain").write_text(
        "leanprover/lean4:v4.30.0-rc2\n",
        encoding="utf-8",
    )
    nested_context = {
        "semantic_primitive": "good_rank_event",
        "source_anchors": [
            {
                "kind": "pseudo_formal_block",
                "id": "pf:block:good_rank_event",
                "excerpt": "rank event source block",
            }
        ],
        "source_anchor_context": [
            {
                "source": "candidate_definition_request.required_anchor_bindings",
                "kind": "required_anchor_binding",
                "required_anchor_name": "q_hat",
                "actual_anchor_name": "q",
                "semantic_anchor_name": "q_hat",
                "name": "q",
                "type": "Real",
                "role": "threshold_function_anchor",
                "binder": {
                    "name": "q",
                    "type": "Real",
                    "role": "threshold_function_anchor",
                },
            }
        ],
        "source_anchor_context_rows": 1,
        "candidate_definition_request": {
            "request_kind": "source_theorem_exact_semantic_definition_candidate",
            "placeholder_symbol": "good_rank_event",
            "required_anchor_names": ["q_hat"],
            "available_anchor_names": ["q", "q_hat"],
            "missing_required_anchor_names": [],
            "required_anchor_bindings": [
                {
                    "required_anchor_name": "q_hat",
                    "actual_anchor_name": "q",
                    "match_kind": "source_anchor_role",
                    "role": "threshold_function_anchor",
                    "binder": {
                        "name": "q",
                        "type": "Real",
                        "role": "threshold_function_anchor",
                    },
                }
            ],
            "required_binders": [
                {
                    "name": "q",
                    "type": "Real",
                    "role": "threshold_function_anchor",
                }
            ],
        },
    }
    tasks = tmp_path / "environment_tasks.jsonl"
    _write_environment_task(
        tasks,
        project=project,
        candidate=candidate,
    )
    task_row = json.loads(tasks.read_text(encoding="utf-8"))
    task_row["placeholder_symbol"] = "good_rank_event"
    task_row["candidate_definition_request"] = {}
    task_row["input_summary"] = {
        "exact_semantic_definition_context": nested_context,
    }
    tasks.write_text(json.dumps(task_row, sort_keys=True) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
        out_dir=tmp_path / "out",
        environment_tasks_jsonl=tasks,
    )

    results = [
        json.loads(line)
        for line in Path(
            manifest["environment_repair_results_jsonl"]
        ).read_text().splitlines()
    ]
    assert results[0]["source_anchor_context"][0]["actual_anchor_name"] == "q"
    assert results[0]["source_anchor_context_rows"] == 1
    assert results[0]["source_anchors"][0]["id"] == "pf:block:good_rank_event"
    assert results[0]["candidate_definition_request"][
        "required_anchor_bindings"
    ][0]["actual_anchor_name"] == "q"
    assert results[0]["candidate_definition_request"]["placeholder_symbol"] == (
        "good_rank_event"
    )

    learning_rows = [
        json.loads(line)
        for line in Path(manifest["runtime_learning_rows_jsonl"]).read_text().splitlines()
    ]
    assert learning_rows[0]["source_anchor_context"][0]["name"] == "q"
    assert learning_rows[0]["candidate_definition_request"]["required_binders"][0][
        "name"
    ] == "q"
    assert learning_rows[0]["input_summary"]["source_anchor_context"][0][
        "actual_anchor_name"
    ] == "q"
    assert learning_rows[0]["input_summary"]["candidate_definition_request"][
        "required_anchor_bindings"
    ][0]["actual_anchor_name"] == "q"


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


def test_lean_environment_repair_executor_preserves_pseudo_formal_origin(
    tmp_path: Path,
) -> None:
    project = tmp_path / "LeanProject"
    candidate = project / "StatInference" / "Conformal" / "Block.lean"
    mathlib = project / ".lake" / "packages" / "mathlib"
    candidate.parent.mkdir(parents=True)
    mathlib.mkdir(parents=True)
    candidate.write_text("import StatInference.Missing\n", encoding="utf-8")
    (project / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    (project / "lean-toolchain").write_text(
        "leanprover/lean4:v4.31.0\n",
        encoding="utf-8",
    )
    (project / "lake-manifest.json").write_text("{}", encoding="utf-8")
    pseudo_formal_origin = {
        "source_pseudo_formal_work_order_id": (
            "pseudo_formal_work_order:35f0c7e436caf8c7"
        ),
        "source_pseudo_formal_block_id": "blk_exchangeable_setup",
        "source_pseudo_formal_packet_id": "pseudo_formal_packet:split",
        "source_pseudo_formal_prompt_scaffold_origin": {
            "artifact_kind": "PseudoFormalPromptScaffoldOrigin",
            "scaffold_kind": "pseudo_formalization_required_copy_fragment",
            "source": "FormalizerPrompt",
            "required_output_key": "pseudo_formal_proof_packets",
            "copy_fragment_id": "pseudo_formal_copy_fragment:exchangeable",
            "proof_evidence_status": (
                "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
            ),
        },
        "source_prompt_scaffold_kind": (
            "pseudo_formalization_required_copy_fragment"
        ),
        "source_prompt_scaffold_id": "pseudo_formal_copy_fragment:exchangeable",
        "source_prompt_scaffold_required_output_key": (
            "pseudo_formal_proof_packets"
        ),
        "source_formalizer_proposal_id": "formalizer_proposal:split",
        "pseudo_formal_method_contract_id": (
            "pseudo_formalization_block_verification_calibration_v1"
        ),
        "pseudo_formal_pipeline_stage": "pseudo_formal_block_routing",
        "pseudo_formal_proof_evidence_status": (
            "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
        ),
    }
    task = {
        "schema_version": 1,
        "artifact_kind": (
            "SourceTheoremExactSemanticDefinitionLeanEnvironmentRepairTask"
        ),
        "environment_repair_task_id": "lean-env-repair:blk_exchangeable_setup",
        "question_id": "conformal_prediction_coverage",
        "target_theorem_name": "split_conformal_coverage",
        "target_ids": ["split_conformal_coverage"],
        "placeholder_symbol": "blk_exchangeable_setup",
        "candidate_source_file": str(candidate),
        "candidate_lean_project_hint": str(project),
        "failure_classification": "lean_import_environment_missing",
        "local_lean_diagnostics": [
            f"{candidate}:1:0: error: unknown module prefix 'StatInference'",
            "No directory 'StatInference' or file 'StatInference.olean' in the search path entries:",
        ],
        "proof_evidence_status": (
            "EXACT_SEMANTIC_DEFINITION_LEAN_ENVIRONMENT_REPAIR_TASK_NOT_PROOF_EVIDENCE"
        ),
        **pseudo_formal_origin,
    }
    tasks = tmp_path / "environment_tasks.jsonl"
    tasks.write_text(json.dumps(task) + "\n", encoding="utf-8")

    manifest = run_source_theorem_exact_semantic_definition_lean_environment_repair_executor(
        out_dir=tmp_path / "out",
        environment_tasks_jsonl=tasks,
    )

    assert manifest["n_tasks_from_pseudo_formal"] == 1
    assert manifest["n_results_from_pseudo_formal"] == 1
    assert manifest["source_pseudo_formal_work_order_ids"] == [
        "pseudo_formal_work_order:35f0c7e436caf8c7"
    ]
    assert manifest["source_pseudo_formal_block_ids"] == [
        "blk_exchangeable_setup"
    ]
    assert manifest["source_prompt_scaffold_ids"] == [
        "pseudo_formal_copy_fragment:exchangeable"
    ]
    assert manifest["source_prompt_scaffold_kinds"] == [
        "pseudo_formalization_required_copy_fragment"
    ]
    assert manifest["source_theorem_ready_for_exact_proof_body"] is False
    output_paths = [
        Path(manifest["environment_repair_results_jsonl"]),
        Path(manifest["runtime_learning_rows_jsonl"]),
    ]
    for output_path in output_paths:
        rows = [
            json.loads(line)
            for line in output_path.read_text(encoding="utf-8").splitlines()
        ]
        row = rows[0]
        assert row["source_pseudo_formal_work_order_id"] == (
            "pseudo_formal_work_order:35f0c7e436caf8c7"
        )
        assert row["source_pseudo_formal_block_id"] == "blk_exchangeable_setup"
        assert row["source_pseudo_formal_packet_id"] == "pseudo_formal_packet:split"
        assert row["source_pseudo_formal_prompt_scaffold_origin"][
            "scaffold_kind"
        ] == "pseudo_formalization_required_copy_fragment"
        assert row["source_prompt_scaffold_id"] == (
            "pseudo_formal_copy_fragment:exchangeable"
        )
        assert row["source_prompt_scaffold_required_output_key"] == (
            "pseudo_formal_proof_packets"
        )
        assert row["source_formalizer_proposal_id"] == "formalizer_proposal:split"
        assert row["pseudo_formal_method_contract_id"] == (
            "pseudo_formalization_block_verification_calibration_v1"
        )
        assert row["pseudo_formal_pipeline_stage"] == "pseudo_formal_block_routing"
        assert row["pseudo_formal_proof_evidence_status"] == (
            "PSEUDO_FORMAL_VERIFICATION_NOT_PROOF_EVIDENCE"
        )
        assert row["source_theorem_kernel_verified"] is False
        assert row["semantic_definition_kernel_verified"] is False
        assert row["source_theorem_ready_for_exact_proof_body"] is False
        assert "KERNEL_VERIFIED" not in row["proof_evidence_status"]
        input_summary = row.get("input_summary", {})
        if isinstance(input_summary, dict) and input_summary:
            assert input_summary["source_pseudo_formal_work_order_id"] == (
                "pseudo_formal_work_order:35f0c7e436caf8c7"
            )
            assert input_summary["source_pseudo_formal_block_id"] == (
                "blk_exchangeable_setup"
            )
            assert input_summary["source_prompt_scaffold_id"] == (
                "pseudo_formal_copy_fragment:exchangeable"
            )
            assert input_summary["source_theorem_ready_for_exact_proof_body"] is False


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
