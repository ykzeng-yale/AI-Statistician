from __future__ import annotations

import hashlib
import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

import ai_statistician.research_gold_evaluation as gold_evaluation_module
from ai_statistician.agent_runtime import load_persisted_runtime_result
from ai_statistician.cli import _post_runtime_gold_evaluation_results
from ai_statistician.fingerprint import stable_hash
from ai_statistician.estimator_interface_contract import (
    frozen_estimator_execution_contract_id,
)
from ai_statistician.research_gold_evaluation import (
    evaluate_research_gold_benchmark,
    validate_research_gold_benchmark_activation,
    validate_research_gold_benchmark_manifest,
)
from ai_statistician.research_agent_runtime import (
    ResearchAgentRuntimeConfig,
    run_research_agent_runtime,
)
from ai_statistician.research_evaluation import research_evaluation_evidence_hash
from ai_statistician.scientific_sandbox import (
    ScientificEstimatorBinding,
    discover_scientific_sandbox_runtime,
)
from ai_statistician.scientific_project import scientific_project_hash
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_CONTENT_AUTHORITY,
    THEORY_WORKSPACE_HANDOFF_ROLE,
    theory_workspace_document_manifest,
)


GOLD_MANIFEST = Path(
    "tests/fixtures/research_gold/mock_gold_manifest.json"
)
QUESTION_ID = "heteroskedastic_covariance_known_result"
VISIBLE_QUESTION = json.loads(
    Path("benchmarks/research_l0_questions_20260814.json").read_text()
)["questions"][0]
SOURCE_REPLICATION_TASK_INTENT = {
    "source_replication": "required",
    "theory": "not_applicable",
    "scientific_code": "not_applicable",
    "empirical": "not_applicable",
    "formal": "not_applicable",
    "novelty": "not_applicable",
    "unresolved_gaps": "required",
}


def test_gold_authority_is_not_part_of_agent_runtime_config() -> None:
    assert "research_gold_manifest" not in (
        ResearchAgentRuntimeConfig.__dataclass_fields__
    )
    assert "research_gold_manifest" not in inspect.signature(
        run_research_agent_runtime
    ).parameters


def test_hc0_visible_statement_distinguishes_finite_and_limit_covariance() -> None:
    description = str(VISIBLE_QUESTION["description"])

    assert "V_HC0 estimates the covariance of beta_hat and is order n^(-1)" in (
        description
    )
    assert "n V_HC0 consistently estimates" in description
    assert "rather than treating full rank at each finite n as sufficient" in (
        description
    )


def test_gold_preflight_descriptor_exposes_no_hidden_evaluator_payload() -> None:
    descriptor = validate_research_gold_benchmark_manifest(GOLD_MANIFEST)

    assert descriptor["active_task_ids"] == [QUESTION_ID]
    serialized = json.dumps(descriptor)
    assert "harness_path" not in serialized
    assert "harness_sha256" not in serialized
    assert "acceptance_checks" not in serialized
    assert "direct_reference_accuracy" not in serialized
    assert "1e-08" not in serialized


def test_local_gold_schema_binds_both_runtime_and_private_reviewer(tmp_path: Path) -> None:
    path = _schema_v4_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text())
    policy = {"provider": "local", "model": "Qwen3-4B-Instruct-2507",
              "model_tier": "local", "automatic_tier_escalation_allowed": False}
    manifest["schema_version"] = 5
    manifest["model_policy"] = policy
    evaluator = manifest["active_tasks"][0]["hidden_theory_semantic_evaluator"]
    evaluator.update(policy)
    path.write_text(json.dumps(manifest))
    assert validate_research_gold_benchmark_manifest(path)["active_task_ids"] == [QUESTION_ID]
    original = path.read_bytes()
    evaluator["provider"] = "anthropic"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="exact model without escalation"):
        validate_research_gold_benchmark_manifest(path)
    path.write_bytes(original)
    with pytest.raises(ValueError, match="model policy differs"):
        validate_research_gold_benchmark_activation(
            path, evaluation_model_policy={**policy, "model": "another-model"},
        )
    assert path.read_bytes() == original


def test_local_runtime_cannot_reuse_a_legacy_gold_policy(tmp_path: Path) -> None:
    path = _schema_v4_gold_manifest(tmp_path)
    original = path.read_bytes()
    with pytest.raises(ValueError, match="historical qualifications cannot be reused"):
        validate_research_gold_benchmark_activation(path, evaluation_model_policy={
            "provider": "local", "model": "Qwen3-4B-Instruct-2507", "model_tier": "local",
        })
    assert path.read_bytes() == original


def test_gold_preflight_rejects_missing_selected_task_before_product_output(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "must-not-exist"
    manifest = _schema_v3_gold_manifest(tmp_path)

    with pytest.raises(ValueError, match="absent from the selected question set"):
        validate_research_gold_benchmark_activation(
            manifest,
            visible_questions={},
        )

    assert not out_dir.exists()


def test_post_runtime_gold_loader_rehydrates_exact_artifact_hashes(
    tmp_path: Path,
) -> None:
    artifact = {
        "artifact_kind": "RuntimeQuestionMetadata",
        "question": {"id": QUESTION_ID},
    }
    artifact_hash = stable_hash(artifact)
    blob_path = tmp_path / "artifact.json"
    blob_path.write_text(json.dumps(artifact), encoding="utf-8")
    reference = {
        "artifact_kind": "RuntimeArtifactRef",
        "artifact_id": "question:1",
        "content_hash": artifact_hash,
        "content_hash_algorithm": "sha256_stable_json_v1",
        "payload_kind": "RuntimeQuestionMetadata",
        "path": blob_path.name,
    }
    index_path = tmp_path / "artifact-index.json"
    index_path.write_text(
        json.dumps(
            {
                "artifact_kind": "RuntimeArtifactStoreIndex",
                "artifacts": {"question:1": reference},
            }
        ),
        encoding="utf-8",
    )
    result_path = tmp_path / "runtime_result.json"
    result_path.write_text(
        json.dumps(
            {
                "blackboard_artifact_payload_policy": "content_addressed_refs",
                "blackboard_artifact_store_index": index_path.name,
                "blackboard": {"artifacts": {"question:1": reference}},
            }
        ),
        encoding="utf-8",
    )

    results = _post_runtime_gold_evaluation_results(
        {"artifacts": {"per_question_results": [str(result_path)]}}
    )

    assert results[0]["blackboard"]["artifacts"] == {"question:1": artifact}
    assert research_evaluation_evidence_hash(results[0]) == (
        research_evaluation_evidence_hash(
            {"blackboard": {"artifacts": {"question:1": artifact}}}
        )
    )
    assert load_persisted_runtime_result(result_path) == results[0]

    blob_path.write_text(json.dumps({**artifact, "tampered": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="artifact payload hash mismatch"):
        _post_runtime_gold_evaluation_results(
            {"artifacts": {"per_question_results": [str(result_path)]}}
        )

    blob_path.write_text(json.dumps(artifact), encoding="utf-8")
    index_path.write_text(
        json.dumps({"artifact_kind": "RuntimeArtifactStoreIndex", "artifacts": {}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="artifact store index mismatch"):
        load_persisted_runtime_result(result_path)


def _model_source() -> str:
    return """
def run_estimator(request):
    return {
        "coefficients": [0.0, 0.0],
        "covariance": [[0.0, 0.0], [0.0, 0.0]],
        "standard_errors": [0.0, 0.0],
    }

def run_sandbox(seed, replicates):
    return {"seed": seed, "replicates": replicates}
"""


def _runtime_result(
    *, include_handoff: bool = True, direct_handoff: bool = False
) -> dict:
    source = _model_source()
    project_hash = scientific_project_hash(language="python", code=source)
    accepted_id = "accepted_algorithm_handoff:test"
    implementation_id = "accepted_implementation_interface_handoff:test"
    accepted = {
        "artifact_kind": "RuntimeAcceptedAlgorithmHandoff",
        "handoff_id": accepted_id,
        "source": "accepted_algorithm_semantic_review_materialization",
        "question_id": QUESTION_ID,
        "exact_algorithm_artifacts": [
            {
                "estimator_id": "est_ols_hc0_covariance",
                "language": "python",
                "dependencies": ["numpy"],
                "exact_source_code": source,
                "exact_source_hash": stable_hash(source),
                "exact_project_files": [],
                "exact_project_hash": project_hash,
            }
        ],
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }
    implementation = {
        "artifact_kind": "RuntimeAcceptedImplementationInterfaceHandoff",
        "question_id": QUESTION_ID,
        "source_accepted_algorithm_handoff_id": accepted_id,
        "source_accepted_algorithm_handoff_hash": stable_hash(accepted),
    }
    artifacts = {
        f"runtime_question_metadata:{QUESTION_ID}": {
            "artifact_kind": "RuntimeQuestionMetadata",
            "question": VISIBLE_QUESTION,
        }
    }
    produced = []
    if include_handoff:
        artifacts[accepted_id] = accepted
        if direct_handoff:
            produced.append(accepted_id)
        else:
            artifacts[implementation_id] = implementation
            produced.append(implementation_id)
    return {
        "status": "ACCEPTED",
        "traces": [{"produced_artifact_ids": produced}],
        "blackboard": {"artifacts": artifacts},
    }


def test_hidden_evaluator_accepts_direct_reviewed_algorithm_handoff() -> None:
    result = _runtime_result(direct_handoff=True)

    handoff_id, handoff, errors = (
        gold_evaluation_module._latest_accepted_algorithm_handoff(
            result,
            result["blackboard"]["artifacts"],
        )
    )

    assert errors == []
    assert handoff_id == "accepted_algorithm_handoff:test"
    assert handoff["exact_algorithm_artifacts"][0]["exact_source_code"] == (
        _model_source()
    )


def _runtime_result_with_accepted_theory(
    *,
    document_workspace: Path | None = None,
    estimator_specs: list[dict] | None = None,
) -> dict:
    result = _runtime_result()
    artifacts = result["blackboard"]["artifacts"]
    theory_id = "theory_derivation:test"
    preflight_id = "architect_theory_execution_preflight:test"
    acceptance_id = "architect_theory_execution_preflight_acceptance:test"
    theory = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": theory_id,
        "serious_theory_mode": True,
        "theory_derivation_packet": {"mock_claim": "candidate-owned content"},
    }
    if estimator_specs is not None:
        theory["estimator_specs"] = deepcopy(estimator_specs)
    if document_workspace is not None:
        documents = {
            "derivations/C1.md": "# C1\n\nThe candidate-owned derivation.\n"
        }
        for relative_path, content in documents.items():
            target = document_workspace / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        theory["theory_workspace_manifest"] = theory_workspace_document_manifest(
            documents,
            workspace_dir=document_workspace,
        )
        theory["theory_content_authority"] = THEORY_WORKSPACE_CONTENT_AUTHORITY
        theory["structured_handoff_role"] = THEORY_WORKSPACE_HANDOFF_ROLE
    preflight = {
        "artifact_kind": "ArchitectTheoryExecutionPreflightReviewPacket",
        "source_theory_packet_id": theory_id,
        "source_theory_packet_hash": stable_hash(theory),
        "overall_verdict": "ACCEPT",
        "active_unresolved_finding_ids": [],
    }
    acceptance = {
        "artifact_kind": "RuntimeArchitectTheoryExecutionPreflightAcceptance",
        "source_theory_packet_id": theory_id,
        "source_theory_packet_hash": stable_hash(theory),
        "preflight_packet_id": preflight_id,
        "preflight_packet_hash": stable_hash(preflight),
    }
    artifacts[theory_id] = theory
    artifacts[preflight_id] = preflight
    artifacts[acceptance_id] = acceptance
    return result


def _research_summary(runtime_result: dict | None = None) -> dict:
    runtime_result = runtime_result or _runtime_result()
    row = {
        "question_id": QUESTION_ID,
        "runtime_evidence_hash": research_evaluation_evidence_hash(runtime_result),
        "research_eval_complete": True,
        "requirements": {
            "serious_theory_completed": True,
            "theory_preexecution_review_accepted": True,
            "generated_algorithm_executed_and_passed": True,
            "algorithm_semantic_review_accepted": True,
            "generated_simulation_executed_and_passed": True,
            "simulation_metric_evidence_nonvacuous_and_bound": True,
            "simulation_semantic_review_accepted": True,
            "critic_research_acceptance": True,
            "critic_unresolved_gap_disclosure_present": True,
        },
    }
    row["summary_row_hash"] = stable_hash(row)
    return {"rows": [row]}


def _passing_harness(**kwargs) -> dict:
    binding = kwargs["estimator_binding"]
    assert binding.artifact_id == "est_ols_hc0_covariance"
    assert binding.code_hash == stable_hash(binding.code)
    assert "expected" not in kwargs["harness_code"]
    return {
        "execution_attempted": True,
        "returncode": 0,
        "errors": [],
        "estimator_binding_errors": [],
        "estimator_runtime_errors": [],
        "result_parse_error": "",
        "result_hash": "hidden-result-hash",
        "estimator_invocation_counts": {
            "est_ols_hc0_covariance": 4,
        },
        "metrics": {
            "hidden_cases_total": 4,
            "hidden_cases_passed": 4,
            "max_direct_reference_error": 0.0,
            "permutation_invariance_error": 0.0,
            "response_scale_equivariance_error": 0.0,
            "exact_fit_error": 0.0,
            "all_outputs_finite": True,
            "empirical_gold_ok": True,
        },
    }


def _passing_artifact_harness(**kwargs) -> dict:
    candidate = kwargs["candidate_artifact"]
    assert candidate["artifact_kind"] == "TheoryDerivationPacket"
    return {
        "execution_attempted": True,
        "returncode": 0,
        "errors": [],
        "estimator_binding_errors": [],
        "estimator_runtime_errors": [],
        "result_parse_error": "",
        "result_hash": "hidden-theory-result-hash",
        "metrics": {"theory_gold_ok": True},
    }


def _fixture_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _full_task_gold_manifest(tmp_path: Path) -> Path:
    manifest = json.loads(GOLD_MANIFEST.read_text())
    task = manifest["active_tasks"][0]
    task["scoring_scope"] = "full_task"
    theory_harness = Path(
        "tests/fixtures/research_gold/mock_theory_harness.py"
    )
    empirical_harness = Path(
        "tests/fixtures/research_gold/mock_empirical_harness.py"
    )
    task["hidden_theory_evaluator"] = {
        "harness_path": str(theory_harness),
        "harness_sha256": _fixture_sha256(theory_harness),
        "language": "python",
        "dependencies": [],
        "seed": 1,
        "replicates": 1,
        "timeout_seconds": 10,
        "acceptance_checks": [
            {
                "check_id": "private_theory_check",
                "path": ["theory_gold_ok"],
                "operator": "eq",
                "expected": True,
            }
        ],
    }
    task["hidden_empirical_evaluator"] = {
        "required_estimator_id": "est_ols_hc0_covariance",
        "harness_path": str(empirical_harness),
        "harness_sha256": _fixture_sha256(empirical_harness),
        "language": "python",
        "dependencies": [],
        "seed": 2,
        "replicates": 25,
        "timeout_seconds": 10,
        "acceptance_checks": [
            {
                "check_id": "private_empirical_check",
                "path": ["empirical_gold_ok"],
                "operator": "eq",
                "expected": True,
            }
        ],
    }
    path = tmp_path / "full-task-gold.json"
    path.write_text(json.dumps(manifest))
    return path


def _add_semantic_theory_evaluator(path: Path, tmp_path: Path) -> Path:
    reference = tmp_path / "private-reference.md"
    reference.write_text("# Reference\n\nA correct claim.\n")
    rubric = tmp_path / "private-rubric.json"
    rubric.write_text(
        json.dumps(
            {
                "rubric_id": "private-rubric",
                "claims": [
                    {
                        "claim_id": "private-claim",
                        "criterion": "The candidate is semantically correct.",
                    }
                ],
            }
        )
    )
    calibration = tmp_path / "private-calibration.json"
    calibration.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "private-case-a",
                        "expected_status": "PASS",
                        "documents": [{"path": "a.md", "content": "correct"}],
                    },
                    {
                        "case_id": "private-case-b",
                        "expected_status": "FAIL",
                        "documents": [{"path": "b.md", "content": "incorrect"}],
                    },
                ]
            }
        )
    )
    manifest = json.loads(path.read_text())
    manifest["active_tasks"][0]["hidden_theory_semantic_evaluator"] = {
        "provider": "anthropic",
        "model_tier": "haiku",
        "model": "claude-haiku-4-5-20251001",
        "automatic_tier_escalation_allowed": False,
        "max_tokens": 2000,
        "timeout_seconds": 30,
        "reference_documents": [
            {
                "document_id": "private-reference",
                "path": str(reference),
                "sha256": _fixture_sha256(reference),
            }
        ],
        "rubric_path": str(rubric),
        "rubric_sha256": _fixture_sha256(rubric),
        "calibration_cases_path": str(calibration),
        "calibration_cases_sha256": _fixture_sha256(calibration),
    }
    path.write_text(json.dumps(manifest))
    return path


def _source_replication_component_manifest(tmp_path: Path) -> Path:
    manifest = json.loads(GOLD_MANIFEST.read_text())
    task = manifest["active_tasks"][0]
    task["scoring_scope"] = "component"
    task.pop("hidden_algorithm_evaluator", None)
    task["task_intent"] = dict(SOURCE_REPLICATION_TASK_INTENT)
    harness = Path("tests/fixtures/research_gold/mock_theory_harness.py")
    task["hidden_source_replication_evaluator"] = {
        "harness_path": str(harness),
        "harness_sha256": _fixture_sha256(harness),
        "language": "python",
        "dependencies": [],
        "seed": 0,
        "replicates": 1,
        "timeout_seconds": 10,
        "acceptance_checks": [
            {
                "check_id": "private_source_identity",
                "path": ["source_gold_ok"],
                "operator": "eq",
                "expected": True,
            }
        ],
    }
    path = tmp_path / "source-replication-component-gold.json"
    path.write_text(json.dumps(manifest))
    return path


def _add_source_report_semantic_evaluator(path: Path, tmp_path: Path) -> Path:
    reference = tmp_path / "private-source-report-reference.md"
    reference.write_text(
        "# Reference\n\nThe immutable published source executed successfully.\n"
    )
    rubric = tmp_path / "private-source-report-rubric.json"
    rubric.write_text(
        json.dumps(
            {
                "rubric_id": "private-source-report-rubric",
                "claims": [
                    {
                        "claim_id": "private-source-method-identity",
                        "criterion": (
                            "The report identifies the published method and result "
                            "without substituting a nearby model."
                        ),
                    }
                ],
            }
        )
    )
    calibration = tmp_path / "private-source-report-calibration.json"
    calibration.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "private-source-report-correct",
                        "expected_status": "PASS",
                        "documents": [
                            {"path": "correct.md", "content": "correct method"}
                        ],
                    },
                    {
                        "case_id": "private-source-report-wrong-method",
                        "expected_status": "FAIL",
                        "documents": [
                            {"path": "wrong.md", "content": "nearby wrong method"}
                        ],
                    },
                ]
            }
        )
    )
    manifest = json.loads(path.read_text())
    manifest["active_tasks"][0]["hidden_source_report_semantic_evaluator"] = {
        "provider": "anthropic",
        "model_tier": "haiku",
        "model": "claude-haiku-4-5-20251001",
        "automatic_tier_escalation_allowed": False,
        "candidate_adjudication_strategy": "integrated_single",
        "max_tokens": 2000,
        "timeout_seconds": 30,
        "reference_documents": [
            {
                "document_id": "private-source-report-reference",
                "path": str(reference),
                "sha256": _fixture_sha256(reference),
            }
        ],
        "rubric_path": str(rubric),
        "rubric_sha256": _fixture_sha256(rubric),
        "calibration_cases_path": str(calibration),
        "calibration_cases_sha256": _fixture_sha256(calibration),
    }
    path.write_text(json.dumps(manifest))
    return path


def _runtime_result_with_source_replication(
    *,
    workspace_dir: Path,
    valid_hash: bool = True,
    include_checkpoint: bool = True,
) -> dict:
    result = _runtime_result(include_handoff=False)
    body = {
        "schema_version": 1,
        "artifact_kind": "SourceReplicationManifest",
        "artifact_identity_schema_version": 2,
        "artifact_id": "source_replication:test",
        "question_id": QUESTION_ID,
        "benchmark_id": "published-source-test",
        "execution_status": "EXECUTED",
        "execution_attempted": True,
        "returncode": 0,
        "errors": [],
        "raw_stdout": "published output\n",
        "raw_stderr": "",
        "stdout_sha256": hashlib.sha256(b"published output\n").hexdigest(),
        "source_mutated": False,
        "staged_source_inputs_mutated": False,
        "unexpected_workspace_artifacts": [],
        "unexpected_execution_artifacts": [],
        "runtime_edited_source": False,
        "command_owned_by_model": False,
        "runtime_generated": True,
        "model_authored": False,
        "proof_evidence_status": "SOURCE_REPLICATION_EXECUTION_NOT_PROOF_EVIDENCE",
    }
    manifest = {
        **body,
        "manifest_hash": stable_hash(body) if valid_hash else "invalid",
    }
    artifacts = result["blackboard"]["artifacts"]
    artifacts[manifest["artifact_id"]] = manifest
    if not include_checkpoint:
        return result

    report_path = "replication/report.md"
    report_content = (
        "# Published-source replication\n\n"
        "The immutable author source executed successfully.\n"
    )
    report_file = workspace_dir / report_path
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report_content, encoding="utf-8")
    document_manifest = theory_workspace_document_manifest(
        {report_path: report_content},
        workspace_dir=workspace_dir,
    )
    report_document = dict(document_manifest["documents"][0])
    source_ref = {
        "artifact_id": manifest["artifact_id"],
        "manifest_hash": manifest["manifest_hash"],
        "execution_status": manifest["execution_status"],
        "stdout_sha256": manifest["stdout_sha256"],
    }
    checkpoint_body = {
        "schema_version": 1,
        "artifact_kind": "SourceReplicationCheckpoint",
        "question_id": QUESTION_ID,
        "workspace_id": "theory-workspace:test",
        "task_intent": dict(SOURCE_REPLICATION_TASK_INTENT),
        "source_replication_manifest_ref": source_ref,
        "report_document": report_document,
        "unresolved_gaps": [],
        "readiness_rationale": "The exact published source run was inspected.",
        "runtime_edited_source": False,
        "runtime_edited_report": False,
        "model_authored_report": True,
        "proof_evidence_status": (
            "SOURCE_REPLICATION_CHECKPOINT_NOT_PROOF_EVIDENCE"
        ),
        "kernel_verified": False,
    }
    checkpoint_id = "source_replication_checkpoint:" + stable_hash(
        checkpoint_body
    )[:20]
    checkpoint = {**checkpoint_body, "checkpoint_id": checkpoint_id}
    workspace_evidence_id = "source_replication_workspace:test"
    workspace_evidence = {
        "schema_version": 1,
        "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
        "artifact_id": workspace_evidence_id,
        "workspace_id": "theory-workspace:test",
        "question_id": QUESTION_ID,
        "submitted_core_packet_hash": stable_hash(checkpoint),
        "changed_document_paths": [report_path],
        "theory_workspace_manifest": document_manifest,
        "source_replication_refs": [source_ref],
        "disposition": "SOURCE_REPLICATION_CHECKPOINT_COMMITTED",
        "checkpoint_committed": True,
        "model_owned_theory": False,
        "model_owned_source_report": True,
        "runtime_edited_theory": False,
        "runtime_edited_source": False,
        "accepted": True,
        "proof_evidence_status": (
            "SOURCE_REPLICATION_WORKSPACE_NOT_PROOF_EVIDENCE"
        ),
        "kernel_verified": False,
    }
    artifacts[workspace_evidence_id] = workspace_evidence
    artifacts[checkpoint_id] = {
        **checkpoint,
        "workspace_evidence_id": workspace_evidence_id,
        "workspace_evidence_hash": stable_hash(workspace_evidence),
        "runtime_completion_status": (
            "SOURCE_EXECUTION_RECORDED_REQUIRES_HIDDEN_EVALUATION"
        ),
        "boundary": "source replication is not proof evidence",
    }
    return result


def test_gold_evaluator_scores_only_accepted_exact_source(tmp_path: Path) -> None:
    runtime_result = _runtime_result()
    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=GOLD_MANIFEST,
        out_dir=tmp_path,
        run_harness=_passing_harness,
    )

    assert result["configured"] is True
    assert result["all_active_tasks_passed"] is False
    assert result["n_tasks_passed"] == 0
    task = result["tasks"][0]
    assert task["runtime_summary_evidence_hash_valid"] is True
    assert task["runtime_summary_row_hash_valid"] is True
    assert task["hidden_harness_estimator_invocation_count"] == 4
    assert task["hidden_checks_passed"] is True
    assert task["dimension_status"]["scientific_code"]["status"] == "passed"
    assert task["dimension_status"]["scientific_code"]["gold_validated"] is True
    assert task["dimension_status"]["theory"]["status"] == (
        "runtime_reviewed_not_gold_validated"
    )
    assert task["dimension_status"]["theory"]["gold_validated"] is False
    assert task["dimension_status"]["empirical"]["status"] == (
        "runtime_accepted_not_gold_validated"
    )
    assert task["task_passed"] is False
    assert task["failure_reasons"] == [
        "required evidence dimension did not pass: theory",
        "required evidence dimension did not pass: empirical",
    ]
    assert all(
        set(row) == {"check_id_hash", "passed"}
        for row in task["hidden_check_results"]
    )
    assert all(
        len(row["check_id_hash"]) == 64
        for row in task["hidden_check_results"]
    )
    persisted = json.loads(
        (tmp_path / "research_capability_gold_evaluation.json").read_text()
    )
    assert persisted["hidden_expected_values_disclosed"] is False
    assert persisted["runtime_feedback_generated"] is False
    assert persisted["benchmark_authority_location_disclosed"] is False
    assert "benchmark_manifest_path" not in persisted
    assert not (tmp_path / "gold_sandbox").exists()
    serialized = json.dumps(persisted)
    assert "all_hidden_cases_pass" not in serialized
    assert "direct_reference_accuracy" not in serialized
    assert '"operator"' not in serialized
    assert '"observed"' not in serialized


def test_gold_evaluator_rejects_summary_from_another_runtime_graph(
    tmp_path: Path,
) -> None:
    runtime_result = _runtime_result()
    summary = _research_summary(runtime_result)
    runtime_result["status"] = "BLOCKED"
    calls = []

    def forbidden_harness(**kwargs) -> dict:
        calls.append(kwargs)
        return _passing_harness(**kwargs)

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=summary,
        benchmark_manifest_path=GOLD_MANIFEST,
        out_dir=tmp_path,
        run_harness=forbidden_harness,
    )

    assert calls == []
    task = result["tasks"][0]
    assert task["runtime_summary_evidence_hash_valid"] is False
    assert task["runtime_summary_row_hash_valid"] is True
    assert task["runtime_research_eval_complete"] is False
    assert task["task_passed"] is False
    assert task["failure_reasons"] == [
        "research summary is not bound to this runtime evidence graph"
    ]


def test_gold_evaluator_rejects_mutated_summary_row(tmp_path: Path) -> None:
    runtime_result = _runtime_result()
    summary = _research_summary(runtime_result)
    summary["rows"][0]["requirements"]["serious_theory_completed"] = False
    calls = []

    def forbidden_harness(**kwargs) -> dict:
        calls.append(kwargs)
        return _passing_harness(**kwargs)

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=summary,
        benchmark_manifest_path=GOLD_MANIFEST,
        out_dir=tmp_path,
        run_harness=forbidden_harness,
    )

    assert calls == []
    task = result["tasks"][0]
    assert task["runtime_summary_evidence_hash_valid"] is True
    assert task["runtime_summary_row_hash_valid"] is False
    assert task["task_passed"] is False


def test_gold_evaluator_rejects_duplicate_runtime_or_summary_identity(
    tmp_path: Path,
) -> None:
    runtime_result = _runtime_result()
    summary = _research_summary(runtime_result)

    with pytest.raises(ValueError, match="duplicate runtime results"):
        evaluate_research_gold_benchmark(
            [runtime_result, deepcopy(runtime_result)],
            research_evaluation_summary=summary,
            benchmark_manifest_path=GOLD_MANIFEST,
            out_dir=tmp_path / "runtime",
            run_harness=_passing_harness,
        )

    ambiguous_result = deepcopy(runtime_result)
    ambiguous_result["blackboard"]["artifacts"]["another-question"] = {
        "artifact_kind": "RuntimeQuestionMetadata",
        "question": {"id": "another-question"},
    }
    with pytest.raises(ValueError, match="multiple question metadata"):
        evaluate_research_gold_benchmark(
            [ambiguous_result],
            research_evaluation_summary=summary,
            benchmark_manifest_path=GOLD_MANIFEST,
            out_dir=tmp_path / "ambiguous",
            run_harness=_passing_harness,
        )

    with pytest.raises(ValueError, match="duplicate research summary rows"):
        evaluate_research_gold_benchmark(
            [runtime_result],
            research_evaluation_summary={
                "rows": [*summary["rows"], deepcopy(summary["rows"][0])]
            },
            benchmark_manifest_path=GOLD_MANIFEST,
            out_dir=tmp_path / "summary",
            run_harness=_passing_harness,
        )


def test_gold_evaluator_binds_the_complete_accepted_project(tmp_path: Path) -> None:
    runtime_result = _runtime_result()
    accepted = runtime_result["blackboard"]["artifacts"][
        "accepted_algorithm_handoff:test"
    ]["exact_algorithm_artifacts"][0]
    support_source = "def identity(value):\n    return value\n"
    project_files = [{"path": "support.py", "content": support_source}]
    project_hash = scientific_project_hash(
        language="python",
        code=accepted["exact_source_code"],
        project_files=project_files,
    )
    accepted["exact_project_files"] = project_files
    accepted["exact_project_hash"] = project_hash
    implementation = runtime_result["blackboard"]["artifacts"][
        "accepted_implementation_interface_handoff:test"
    ]
    implementation["source_accepted_algorithm_handoff_hash"] = stable_hash(
        runtime_result["blackboard"]["artifacts"][
            "accepted_algorithm_handoff:test"
        ]
    )
    captured = {}

    def project_harness(**kwargs) -> dict:
        binding = kwargs["estimator_binding"]
        captured["project_hash"] = binding.project_hash
        captured["project_files"] = binding.project_files
        return _passing_harness(**kwargs)

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=GOLD_MANIFEST,
        out_dir=tmp_path,
        run_harness=project_harness,
    )

    task = result["tasks"][0]
    assert task["evaluated_project_hash"] == project_hash
    assert captured["project_hash"] == project_hash
    assert [row.path for row in captured["project_files"]] == ["support.py"]
    assert captured["project_files"][0].content == support_source


@pytest.mark.parametrize("identity_failure", ["missing", "stale"])
def test_gold_evaluator_rejects_unbound_or_stale_multifile_project(
    tmp_path: Path,
    identity_failure: str,
) -> None:
    runtime_result = _runtime_result()
    accepted = runtime_result["blackboard"]["artifacts"][
        "accepted_algorithm_handoff:test"
    ]["exact_algorithm_artifacts"][0]
    original_files = [
        {"path": "support.py", "content": "VALUE = 1\n"}
    ]
    accepted["exact_project_files"] = deepcopy(original_files)
    if identity_failure == "stale":
        accepted["exact_project_hash"] = scientific_project_hash(
            language="python",
            code=accepted["exact_source_code"],
            project_files=original_files,
        )
        accepted["exact_project_files"][0]["content"] = "VALUE = 2\n"
    implementation = runtime_result["blackboard"]["artifacts"][
        "accepted_implementation_interface_handoff:test"
    ]
    implementation["source_accepted_algorithm_handoff_hash"] = stable_hash(
        runtime_result["blackboard"]["artifacts"][
            "accepted_algorithm_handoff:test"
        ]
    )
    calls = []

    def forbidden_harness(**kwargs) -> dict:
        calls.append(kwargs)
        return _passing_harness(**kwargs)

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=GOLD_MANIFEST,
        out_dir=tmp_path / identity_failure,
        run_harness=forbidden_harness,
    )

    assert calls == []
    assert "accepted estimator project hash is invalid" in result["tasks"][0][
        "failure_reasons"
    ]


def test_gold_evaluator_rejects_unbound_single_file_project(tmp_path: Path) -> None:
    runtime_result = _runtime_result()
    accepted = runtime_result["blackboard"]["artifacts"][
        "accepted_algorithm_handoff:test"
    ]
    accepted["exact_algorithm_artifacts"][0]["exact_project_hash"] = ""
    implementation = runtime_result["blackboard"]["artifacts"][
        "accepted_implementation_interface_handoff:test"
    ]
    implementation["source_accepted_algorithm_handoff_hash"] = stable_hash(
        accepted
    )
    calls = []

    def forbidden_harness(**kwargs) -> dict:
        calls.append(kwargs)
        return _passing_harness(**kwargs)

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=GOLD_MANIFEST,
        out_dir=tmp_path,
        run_harness=forbidden_harness,
    )

    assert calls == []
    assert "accepted estimator project hash is invalid" in result["tasks"][0][
        "failure_reasons"
    ]


def test_source_replication_component_is_scored_post_runtime_without_algorithm(
    tmp_path: Path,
) -> None:
    manifest = _source_replication_component_manifest(tmp_path)

    def source_runner(**kwargs) -> dict:
        candidate = kwargs["candidate_artifact"]
        assert candidate["artifact_kind"] == "SourceReplicationManifest"
        assert candidate["raw_stdout"] == "published output\n"
        assert candidate["command_owned_by_model"] is False
        assert candidate["artifact_identity_schema_version"] == 2
        assert candidate["unexpected_execution_artifacts"] == []
        return {
            "execution_attempted": True,
            "returncode": 0,
            "errors": [],
            "result_parse_error": "",
            "result_hash": "hidden-source-result",
            "metrics": {"source_gold_ok": True},
        }

    result = evaluate_research_gold_benchmark(
        [
            _runtime_result_with_source_replication(
                workspace_dir=tmp_path / "workspace"
            )
        ],
        research_evaluation_summary={"rows": []},
        benchmark_manifest_path=manifest,
        out_dir=tmp_path / "out",
        run_artifact_harness=source_runner,
    )

    task = result["tasks"][0]
    assert task["source_replication_manifest_id"] == "source_replication:test"
    assert task["hidden_source_replication_checks_passed"] is True
    assert task["hidden_source_replication_identity_passed"] is True
    assert task["hidden_source_report_semantic_evaluation_configured"] is False
    assert task["hidden_source_replication_combined_passed"] is True
    assert task["dimension_status"]["source_replication"]["status"] == "passed"
    assert task["dimension_status"]["source_replication"]["gold_validated"] is True
    assert task["source_replication_checkpoint_valid"] is True
    assert task["unresolved_gap_disclosure_present"] is True
    assert task["dimension_status"]["unresolved_gaps"] == {
        "requirement": "required",
        "status": "passed",
        "gold_validated": False,
        "evidence_authority": "source_replication_checkpoint",
    }
    assert task["dimension_status"]["scientific_code"]["gold_validated"] is False
    assert task["dimension_status"]["empirical"]["gold_validated"] is False
    assert task["dimension_status"]["overall_runtime_research_loop"] == {
        "requirement": "not_applicable",
        "status": "not_applicable",
        "gold_validated": False,
        "evidence_authority": "runtime_completion_contract",
    }
    assert task["task_passed"] is True
    assert task["failure_reasons"] == []


def test_gold_evaluator_rejects_unclean_source_execution_before_hidden_harness() -> None:
    body = {
        "artifact_kind": "SourceReplicationManifest",
        "artifact_id": "source_replication:unclean",
        "question_id": QUESTION_ID,
        "execution_status": "FAILED",
        "execution_attempted": True,
        "returncode": 0,
        "errors": [
            "source execution created undeclared output-root artifact: escaped.txt"
        ],
        "source_mutated": False,
        "runtime_edited_source": False,
        "staged_source_inputs_mutated": False,
        "unexpected_workspace_artifacts": [],
        "unexpected_execution_artifacts": ["escaped.txt"],
        "command_owned_by_model": False,
        "runtime_generated": True,
        "model_authored": False,
    }
    manifest = {**body, "manifest_hash": stable_hash(body)}

    artifact_id, artifact, errors = (
        gold_evaluation_module._latest_source_replication_manifest(
            {manifest["artifact_id"]: manifest},
            question_id=QUESTION_ID,
        )
    )

    assert artifact_id == ""
    assert artifact == {}
    assert errors == ["source replication execution is not clean"]


def test_strict_source_replication_gold_rejects_model_selected_command(
    tmp_path: Path,
) -> None:
    runtime_result = _runtime_result_with_source_replication(
        workspace_dir=tmp_path / "workspace"
    )
    manifest = runtime_result["blackboard"]["artifacts"][
        "source_replication:test"
    ]
    manifest.pop("manifest_hash")
    manifest.update({
        "command_owned_by_model": True,
        "command_selection_mode": "model_selected",
        "command_request_hash": "model-command",
        "execution_attempt_id": "source_attempt:1",
    })
    manifest["manifest_hash"] = stable_hash(manifest)
    calls = []

    def forbidden_source_runner(**kwargs) -> dict:
        calls.append(kwargs)
        return {}

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary={"rows": []},
        benchmark_manifest_path=_source_replication_component_manifest(tmp_path),
        out_dir=tmp_path / "out",
        run_artifact_harness=forbidden_source_runner,
    )

    assert calls == []
    task = result["tasks"][0]
    assert task["hidden_source_replication_identity_passed"] is False
    assert task["dimension_status"]["source_replication"]["gold_validated"] is False
    assert task["task_passed"] is False
    assert "source replication manifest lineage is invalid" in task[
        "failure_reasons"
    ]


@pytest.mark.parametrize("language", ["python", "r"])
def test_hidden_artifact_harness_transports_large_candidate_as_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    language: str,
) -> None:
    captured: dict[str, object] = {}

    class _Execution:
        def to_json(self) -> dict:
            return {
                "execution_attempted": True,
                "returncode": 0,
                "errors": [],
                "metrics": {"ok": True},
            }

    def fake_execute(**kwargs):
        captured.update(kwargs)
        return _Execution()

    monkeypatch.setattr(
        gold_evaluation_module,
        "execute_scientific_sandbox",
        fake_execute,
    )
    candidate = {"raw_text": "x" * 200_000}
    result = gold_evaluation_module._run_hidden_artifact_harness(
        sandbox_dir=tmp_path,
        artifact_id="hidden-large-candidate",
        harness_code=(
            "def evaluate_artifact(candidate, seed, replicates):\n"
            "    return {'ok': len(candidate['raw_text']) == 200000}\n"
        ) if language == "python" else (
            "evaluate_artifact <- function(candidate, seed, replicates) {\n"
            "    list(ok=nchar(candidate$raw_text)==200000)\n"
            "}\n"
        ),
        harness_dependencies=(),
        candidate_artifact=candidate,
        seed=1,
        replicates=1,
        timeout_s=10,
        harness_language=language,
    )

    assert result["metrics"] == {"ok": True}
    assert captured["language"] == language
    assert len(str(captured["code"])) < 100_000
    assert "x" * 1_000 not in str(captured["code"])
    input_artifacts = captured["input_artifacts"]
    assert len(input_artifacts) == 1
    assert input_artifacts[0].artifact_id == "candidate-artifact.json"
    assert json.loads(input_artifacts[0].content) == candidate
    assert input_artifacts[0].content_sha256 == hashlib.sha256(
        input_artifacts[0].content.encode("utf-8")
    ).hexdigest()


def test_hidden_artifact_harness_rejects_unknown_language_before_execution(monkeypatch, tmp_path):
    def forbidden(**kwargs):
        raise AssertionError("invalid language must not start an executor")
    monkeypatch.setattr(gold_evaluation_module, "execute_scientific_sandbox", forbidden)
    with pytest.raises(ValueError, match="language must be python or r"):
        gold_evaluation_module._run_hidden_artifact_harness(
            sandbox_dir=tmp_path, artifact_id="opaque", harness_code="opaque",
            harness_dependencies=(), candidate_artifact={"opaque": True},
            seed=1, replicates=1, timeout_s=10, harness_language="unknown",
        )


@pytest.mark.parametrize(
    ("calibrated", "candidate_status", "expected_pass"),
    (
        (True, "PASS", True),
        (False, "PASS", False),
        (True, "FAIL", False),
    ),
)
def test_source_replication_separates_identity_from_report_semantics(
    tmp_path: Path,
    calibrated: bool,
    candidate_status: str,
    expected_pass: bool,
) -> None:
    manifest = _add_source_report_semantic_evaluator(
        _source_replication_component_manifest(tmp_path),
        tmp_path,
    )

    def source_runner(**kwargs) -> dict:
        assert kwargs["candidate_artifact"]["raw_stdout"] == "published output\n"
        return {
            "execution_attempted": True,
            "returncode": 0,
            "errors": [],
            "result_parse_error": "",
            "result_hash": "hidden-source-result",
            "metrics": {"source_gold_ok": True},
        }

    def semantic_runner(**kwargs) -> dict:
        assert kwargs["semantic_artifact_role"] == "source_replication_report"
        assert kwargs["candidate_adjudication_strategy"] == "integrated_single"
        assert kwargs["model"] == "claude-haiku-4-5-20251001"
        assert kwargs["model_tier"] == "haiku"
        assert len(kwargs["candidate_documents"]) == 2
        assert kwargs["candidate_documents"][0]["content"].startswith(
            "# Published-source replication"
        )
        evidence = kwargs["candidate_documents"][1]
        assert evidence["path"] == "evaluator_source_replication_observation.json"
        evidence_body = json.loads(evidence["content"])
        assert evidence_body["hidden_source_replication_metrics"] == {
            "source_gold_ok": True
        }
        assert "raw_stdout" not in evidence_body["source_replication_manifest"]
        assert evidence["sha256"] == hashlib.sha256(
            evidence["content"].encode("utf-8")
        ).hexdigest()
        return {
            "judgment_hash": "private-source-report-result",
            "semantic_judge_calibrated": calibrated,
            "n_calibration_cases": 2,
            "n_calibration_cases_correct": 2 if calibrated else 1,
            "n_claims": 1,
            "candidate_status": candidate_status,
            "candidate_document_status": candidate_status,
            "candidate_integrated_context": True,
            "candidate_integrated_model_calls": 1,
            "candidate_claim_assessments": [
                {
                    "claim_id_hash": stable_hash(
                        "private-source-method-identity"
                    ),
                    "status": (
                        "SATISFIED"
                        if candidate_status == "PASS"
                        else "VIOLATED"
                    ),
                }
            ],
            "passed": calibrated and candidate_status == "PASS",
        }

    result = evaluate_research_gold_benchmark(
        [
            _runtime_result_with_source_replication(
                workspace_dir=tmp_path / "workspace"
            )
        ],
        research_evaluation_summary={"rows": []},
        benchmark_manifest_path=manifest,
        out_dir=tmp_path / "out",
        run_artifact_harness=source_runner,
        run_theory_semantic_judge=semantic_runner,
    )

    task = result["tasks"][0]
    assert task["hidden_source_replication_identity_passed"] is True
    assert task["hidden_source_report_semantic_execution_attempted"] is True
    assert task["hidden_source_report_semantic_judge_calibrated"] is calibrated
    assert task["hidden_source_report_semantic_candidate_status"] == candidate_status
    assert task["hidden_source_report_semantic_candidate_document_status"] == (
        candidate_status
    )
    assert task["hidden_source_report_semantic_candidate_integrated_context"] is True
    assert task["hidden_source_report_semantic_candidate_model_calls"] == 1
    assert task["hidden_source_report_semantic_claim_assessments"] == [
        {
            "claim_id_hash": stable_hash("private-source-method-identity"),
            "status": (
                "SATISFIED" if candidate_status == "PASS" else "VIOLATED"
            ),
        }
    ]
    assert task["hidden_source_report_semantic_passed"] is expected_pass
    assert task["hidden_source_replication_combined_passed"] is expected_pass
    assert task["dimension_status"]["source_replication"]["status"] == (
        "passed" if expected_pass else "failed"
    )
    assert task["task_passed"] is expected_pass
    assert bool(task["source_replication_report_document_hash"])
    serialized = json.dumps(result)
    assert "private-source-method-identity" not in serialized
    assert "private-source-report-correct" not in serialized
    assert "correct method" not in serialized
    assert "source_gold_ok" not in serialized
    if expected_pass:
        assert task["failure_reasons"] == []
    else:
        assert (
            "hidden source-report semantic checks did not all pass"
            in task["failure_reasons"]
        )
        assert (
            "required evidence dimension did not pass: source_replication"
            in task["failure_reasons"]
        )


def test_source_replication_gold_rejects_unbound_runtime_manifest(
    tmp_path: Path,
) -> None:
    result = evaluate_research_gold_benchmark(
        [
            _runtime_result_with_source_replication(
                workspace_dir=tmp_path / "workspace",
                valid_hash=False,
            )
        ],
        research_evaluation_summary={"rows": []},
        benchmark_manifest_path=_source_replication_component_manifest(tmp_path),
        out_dir=tmp_path / "out",
        run_artifact_harness=lambda **kwargs: pytest.fail(
            "hidden evaluator must not run on invalid runtime lineage"
        ),
    )

    task = result["tasks"][0]
    assert task["hidden_source_replication_execution_attempted"] is False
    assert task["task_passed"] is False
    assert "source replication manifest lineage is invalid" in task[
        "failure_reasons"
    ]


def test_source_report_semantics_rejects_tampered_report_before_judgment(
    tmp_path: Path,
) -> None:
    manifest = _add_source_report_semantic_evaluator(
        _source_replication_component_manifest(tmp_path),
        tmp_path,
    )
    runtime_result = _runtime_result_with_source_replication(
        workspace_dir=tmp_path / "workspace"
    )
    report_path = tmp_path / "workspace" / "replication" / "report.md"
    report_path.write_text("# Mutated after checkpoint\n", encoding="utf-8")

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary={"rows": []},
        benchmark_manifest_path=manifest,
        out_dir=tmp_path / "out",
        run_artifact_harness=lambda **kwargs: {
            "execution_attempted": True,
            "returncode": 0,
            "errors": [],
            "result_parse_error": "",
            "result_hash": "hidden-source-result",
            "metrics": {"source_gold_ok": True},
        },
        run_theory_semantic_judge=lambda **kwargs: pytest.fail(
            "tampered report must not reach the hidden semantic judge"
        ),
    )

    task = result["tasks"][0]
    assert task["hidden_source_replication_identity_passed"] is True
    assert task["source_replication_checkpoint_valid"] is False
    assert task["hidden_source_report_semantic_execution_attempted"] is False
    assert task["hidden_source_replication_combined_passed"] is False
    assert task["task_passed"] is False


def test_source_report_semantics_requires_source_identity_evaluator(
    tmp_path: Path,
) -> None:
    manifest = _add_source_report_semantic_evaluator(
        _source_replication_component_manifest(tmp_path),
        tmp_path,
    )
    packet = json.loads(manifest.read_text())
    del packet["active_tasks"][0]["hidden_source_replication_evaluator"]
    manifest.write_text(json.dumps(packet))

    with pytest.raises(
        ValueError,
        match=(
            "source-report semantic evaluation requires "
            "hidden_source_replication_evaluator"
        ),
    ):
        evaluate_research_gold_benchmark(
            [],
            research_evaluation_summary={"rows": []},
            benchmark_manifest_path=manifest,
            out_dir=tmp_path / "out",
        )


def test_source_replication_requires_model_authored_gap_checkpoint(
    tmp_path: Path,
) -> None:
    result = evaluate_research_gold_benchmark(
        [
            _runtime_result_with_source_replication(
                workspace_dir=tmp_path / "workspace",
                include_checkpoint=False,
            )
        ],
        research_evaluation_summary={"rows": []},
        benchmark_manifest_path=_source_replication_component_manifest(tmp_path),
        out_dir=tmp_path / "out",
        run_artifact_harness=lambda **kwargs: {
            "execution_attempted": True,
            "returncode": 0,
            "errors": [],
            "result_parse_error": "",
            "result_hash": "hidden-source-result",
            "metrics": {"source_gold_ok": True},
        },
    )

    task = result["tasks"][0]
    assert task["hidden_source_replication_checks_passed"] is True
    assert task["source_replication_checkpoint_valid"] is False
    assert task["unresolved_gap_disclosure_present"] is False
    assert task["dimension_status"]["unresolved_gaps"]["status"] == "failed"
    assert task["task_passed"] is False
    assert (
        "required evidence dimension did not pass: unresolved_gaps"
        in task["failure_reasons"]
    )


def test_full_task_gold_requires_every_substantive_hidden_authority(
    tmp_path: Path,
) -> None:
    manifest = json.loads(GOLD_MANIFEST.read_text())
    manifest["active_tasks"][0]["scoring_scope"] = "full_task"
    path = tmp_path / "incomplete-full-task.json"
    path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="full_task scoring lacks hidden gold"):
        validate_research_gold_benchmark_manifest(path)


def test_full_task_pass_requires_hidden_theory_code_and_empirical_checks(
    tmp_path: Path,
) -> None:
    manifest = _full_task_gold_manifest(tmp_path)
    sandbox_paths: list[Path] = []

    def scientific_runner(**kwargs) -> dict:
        sandbox_paths.append(Path(kwargs["sandbox_dir"]))
        return _passing_harness(**kwargs)

    def artifact_runner(**kwargs) -> dict:
        sandbox_paths.append(Path(kwargs["sandbox_dir"]))
        return _passing_artifact_harness(**kwargs)

    runtime_result = _runtime_result_with_accepted_theory()
    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=manifest,
        out_dir=tmp_path / "out",
        run_harness=scientific_runner,
        run_artifact_harness=artifact_runner,
    )

    assert result["n_full_task_gold_configured"] == 1
    assert result["n_tasks_passed"] == 1
    assert result["all_active_tasks_passed"] is True
    task = result["tasks"][0]
    assert task["full_task_gold_configured"] is True
    assert task["task_passed"] is True
    assert task["failure_reasons"] == []
    assert task["hidden_theory_checks_passed"] is True
    assert task["hidden_checks_passed"] is True
    assert task["hidden_empirical_checks_passed"] is True
    for dimension in ("theory", "scientific_code", "empirical"):
        assert task["dimension_status"][dimension]["status"] == "passed"
        assert task["dimension_status"][dimension]["gold_validated"] is True
    serialized = json.dumps(result)
    assert "private_theory_check" not in serialized
    assert "private_empirical_check" not in serialized
    assert sandbox_paths
    assert all(not path.exists() for path in sandbox_paths)


def test_gold_manifest_rejects_unsupported_hidden_harness_language(
    tmp_path: Path,
) -> None:
    path = _full_task_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text())
    manifest["active_tasks"][0]["hidden_algorithm_evaluator"]["language"] = (
        "unsupported"
    )
    path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="hidden algorithm language is invalid"):
        validate_research_gold_benchmark_manifest(path)


def test_hidden_scientific_harness_executes_r_harness_with_r_estimator(
    tmp_path: Path,
) -> None:
    runtime = discover_scientific_sandbox_runtime()
    if not runtime.r_available:
        pytest.skip("pinned WebR runtime is not installed on this host")
    estimator = (
        "run_estimator <- function(request) {\n"
        "  list(result=as.numeric(request$value) + 1)\n"
        "}\n"
    )
    harness = (
        "run_sandbox <- function(seed, replicates, estimators) {\n"
        "  observed <- estimators[['candidate']](list(value=seed))\n"
        "  list(exact=abs(observed$result - (seed + 1)) < 1e-12, "
        "replicates=replicates)\n"
        "}\n"
    )

    result = gold_evaluation_module._run_hidden_scientific_harness(
        sandbox_dir=tmp_path,
        artifact_id="gold-r-transport",
        harness_language="r",
        harness_code=harness,
        harness_dependencies=("base", "stats"),
        estimator_binding=ScientificEstimatorBinding(
            artifact_id="candidate",
            language="r",
            code=estimator,
            code_hash=stable_hash(estimator),
            dependencies=("base", "stats"),
        ),
        seed=7,
        replicates=11,
        timeout_s=60,
    )

    assert result["status"] == "EXECUTED"
    assert result["backend"] == "webr"
    assert result["metrics"] == {"exact": True, "replicates": 11}
    assert result["estimator_invocation_counts"] == {"candidate": 1}


def test_theory_only_full_task_counts_hidden_theory_evaluation(
    tmp_path: Path,
) -> None:
    path = _full_task_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text())
    task = manifest["active_tasks"][0]
    task.pop("hidden_algorithm_evaluator", None)
    task.pop("hidden_empirical_evaluator", None)
    task["task_intent"] = {
        "source_replication": "not_applicable",
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
        "novelty": "not_applicable",
        "unresolved_gaps": "required",
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")

    runtime_result = _runtime_result_with_accepted_theory(
        document_workspace=tmp_path / "theory-workspace"
    )
    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=path,
        out_dir=tmp_path / "out",
        run_artifact_harness=_passing_artifact_harness,
    )

    assert result["n_tasks_evaluated"] == 1
    assert result["n_tasks_passed"] == 1
    evaluated = result["tasks"][0]
    assert evaluated["hidden_theory_execution_attempted"] is True
    assert evaluated["dimension_status"]["theory"]["status"] == "passed"
    for dimension in (
        "source_replication",
        "scientific_code",
        "empirical",
        "formal",
        "novelty",
    ):
        assert evaluated["dimension_status"][dimension] == {
            "requirement": "not_applicable",
            "status": "not_applicable",
            "gold_validated": False,
            "evidence_authority": "not_configured",
        }


def test_hidden_theory_evaluator_receives_hash_verified_documents(
    tmp_path: Path,
) -> None:
    manifest = _full_task_gold_manifest(tmp_path)

    def artifact_runner(**kwargs) -> dict:
        candidate = kwargs["candidate_artifact"]
        assert candidate["authoritative_theory_documents"] == [
            {
                "path": "derivations/C1.md",
                "sha256": hashlib.sha256(
                    b"# C1\n\nThe candidate-owned derivation.\n"
                ).hexdigest(),
                "content": "# C1\n\nThe candidate-owned derivation.\n",
            }
        ]
        assert candidate["document_authoritative"] is True
        assert (
            candidate["theory_content_authority"]
            == THEORY_WORKSPACE_CONTENT_AUTHORITY
        )
        assert candidate["structured_handoff_role"] == THEORY_WORKSPACE_HANDOFF_ROLE
        assert candidate["evaluator_document_hydration"][
            "runtime_feedback_generated"
        ] is False
        return _passing_artifact_harness(**kwargs)

    runtime_result = _runtime_result_with_accepted_theory(
        document_workspace=tmp_path / "theory-workspace"
    )
    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=manifest,
        out_dir=tmp_path / "out",
        run_harness=_passing_harness,
        run_artifact_harness=artifact_runner,
    )

    task = result["tasks"][0]
    assert task["accepted_theory_document_count"] == 1
    assert task["accepted_theory_document_set_hash"]
    assert task["hidden_theory_checks_passed"] is True


@pytest.mark.parametrize("calibrated", (True, False))
def test_full_task_theory_requires_calibrated_semantic_judgment(
    tmp_path: Path,
    calibrated: bool,
) -> None:
    manifest = _add_semantic_theory_evaluator(
        _full_task_gold_manifest(tmp_path),
        tmp_path,
    )

    def semantic_runner(**kwargs) -> dict:
        assert kwargs["model"] == "claude-haiku-4-5-20251001"
        assert kwargs["model_tier"] == "haiku"
        assert kwargs["candidate_documents"][0]["content"].startswith("# C1")
        assert len(kwargs["candidate_documents"]) == 2
        interface_document = kwargs["candidate_documents"][1]
        assert interface_document["path"] == (
            "model_authored_estimator_interfaces.json"
        )
        assert hashlib.sha256(
            interface_document["content"].encode("utf-8")
        ).hexdigest() == interface_document["sha256"]
        interface_payload = json.loads(interface_document["content"])
        assert interface_payload["artifact_kind"] == (
            "ModelAuthoredTheorySemanticInterfaceProjection"
        )
        assert interface_payload["content_authority"] == (
            "model_authored_structured_executable_abi"
        )
        assert interface_payload["estimator_specs"][0]["id"] == (
            "est_ols_hc0_covariance"
        )
        assert kwargs["reference_documents"][0]["content"].startswith(
            "# Reference"
        )
        assert len(kwargs["calibration_cases"]) == 2
        return {
            "judgment_hash": "private-semantic-result",
            "semantic_judge_calibrated": calibrated,
            "n_calibration_cases": 2,
            "n_calibration_cases_correct": 2 if calibrated else 1,
            "n_claims": 1,
            "candidate_status": "PASS",
            "candidate_document_status": "PASS",
            "candidate_integrated_context": True,
            "candidate_integrated_model_calls": 1,
            "candidate_claim_assessments": [
                {
                    "claim_id_hash": stable_hash("private-claim"),
                    "status": "SATISFIED",
                }
            ],
            "passed": calibrated,
        }

    runtime_result = _runtime_result_with_accepted_theory(
        document_workspace=tmp_path / "theory-workspace",
        estimator_specs=[
            {
                "id": "est_ols_hc0_covariance",
                "name": "OLS HC0 covariance",
                "inputs": ["design_matrix", "outcomes"],
                "outputs": [
                    "coefficients",
                    "covariance",
                    "standard_errors",
                ],
                "estimator_interface_contract_id": "test-model-contract",
                "estimator_interface_contract": {
                    "request_fields": [
                        {
                            "name": "design_matrix",
                            "binding": "per_replicate_data",
                        },
                        {
                            "name": "outcomes",
                            "binding": "per_replicate_data",
                        },
                    ],
                    "response_fields": [
                        {"name": "coefficients"},
                        {"name": "covariance"},
                        {"name": "standard_errors"},
                    ],
                },
                "termination_guarantee": "Finite linear algebra only.",
            }
        ],
    )
    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=manifest,
        out_dir=tmp_path / "out",
        run_harness=_passing_harness,
        run_artifact_harness=_passing_artifact_harness,
        run_theory_semantic_judge=semantic_runner,
    )

    task = result["tasks"][0]
    assert task["hidden_theory_semantic_execution_attempted"] is True
    assert task["hidden_theory_semantic_judge_calibrated"] is calibrated
    assert task["hidden_theory_semantic_passed"] is calibrated
    assert task["hidden_theory_semantic_candidate_document_status"] == "PASS"
    assert task["hidden_theory_semantic_candidate_integrated_context"] is True
    assert task["hidden_theory_semantic_candidate_model_calls"] == 1
    assert task["hidden_theory_semantic_claim_assessments"] == [
        {
            "claim_id_hash": stable_hash("private-claim"),
            "status": "SATISFIED",
        }
    ]
    assert task["hidden_theory_combined_passed"] is calibrated
    assert task["task_passed"] is calibrated
    serialized = json.dumps(result)
    assert "private-claim" not in serialized
    assert "private-case-a" not in serialized
    assert "A correct claim" not in serialized


def test_hidden_semantic_failure_records_safe_candidate_phase(
    tmp_path: Path,
) -> None:
    manifest = _add_semantic_theory_evaluator(
        _full_task_gold_manifest(tmp_path),
        tmp_path,
    )

    def semantic_runner(**kwargs) -> dict:
        del kwargs
        raise ValueError(
            "invalid hidden candidate semantic judgment: private validator detail"
        )

    runtime_result = _runtime_result_with_accepted_theory(
        document_workspace=tmp_path / "theory-workspace"
    )
    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=manifest,
        out_dir=tmp_path / "out",
        run_harness=_passing_harness,
        run_artifact_harness=_passing_artifact_harness,
        run_theory_semantic_judge=semantic_runner,
    )

    task = result["tasks"][0]
    assert task["hidden_theory_semantic_execution_attempted"] is False
    assert (
        "hidden theory semantic evaluation failed closed: "
        "ValueError:INVALID_CANDIDATE_JUDGMENT"
    ) in task["failure_reasons"]
    assert "private validator detail" not in json.dumps(result)


def test_gold_evaluator_preserves_passed_upstream_dimensions_when_runtime_blocks(
    tmp_path: Path,
) -> None:
    manifest = _full_task_gold_manifest(tmp_path)
    runtime_result = _runtime_result_with_accepted_theory()
    runtime_result["status"] = "BLOCKED"
    summary = _research_summary(runtime_result)
    row = summary["rows"][0]
    row["requirements"].update(
        {
            "generated_simulation_executed_and_passed": False,
            "simulation_metric_evidence_nonvacuous_and_bound": False,
            "simulation_semantic_review_accepted": False,
            "critic_research_acceptance": False,
            "critic_unresolved_gap_disclosure_present": False,
        }
    )
    row["summary_row_hash"] = stable_hash(
        {key: value for key, value in row.items() if key != "summary_row_hash"}
    )

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=summary,
        benchmark_manifest_path=manifest,
        out_dir=tmp_path / "out",
        run_harness=_passing_harness,
        run_artifact_harness=_passing_artifact_harness,
    )

    task = result["tasks"][0]
    assert task["runtime_summary_evidence_hash_valid"] is True
    assert task["runtime_summary_row_hash_valid"] is True
    assert task["runtime_terminal_status"] == "BLOCKED"
    assert task["runtime_terminal_accepted"] is False
    assert task["runtime_research_eval_complete"] is False
    assert task["hidden_checks_passed"] is True
    assert task["dimension_status"]["theory"]["status"] == "passed"
    assert task["dimension_status"]["scientific_code"]["status"] == "passed"
    assert task["dimension_status"]["empirical"]["status"] == (
        "hidden_gold_passed_runtime_not_accepted"
    )
    assert task["dimension_status"]["empirical"]["gold_validated"] is True
    assert task["dimension_status"]["unresolved_gaps"]["status"] == "failed"
    assert task["dimension_status"]["overall_runtime_research_loop"][
        "status"
    ] == "failed"
    assert task["task_passed"] is False
    assert task["failure_reasons"] == [
        "required evidence dimension did not pass: empirical",
        "required evidence dimension did not pass: unresolved_gaps",
        "required evidence dimension did not pass: overall_runtime_research_loop",
    ]


def test_gold_evaluator_fails_closed_without_accepted_source(
    tmp_path: Path,
) -> None:
    runtime_result = _runtime_result(include_handoff=False)
    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(runtime_result),
        benchmark_manifest_path=GOLD_MANIFEST,
        out_dir=tmp_path,
        run_harness=_passing_harness,
    )

    task = result["tasks"][0]
    assert task["hidden_harness_execution_attempted"] is False
    assert task["task_passed"] is False
    assert task["failure_reasons"] == [
        "no independently accepted algorithm handoff was observed"
    ]


def test_gold_evaluator_rejects_tampered_visible_question_hash(
    tmp_path: Path,
) -> None:
    manifest = json.loads(GOLD_MANIFEST.read_text())
    manifest["active_tasks"][0]["visible_question_hash"] = "wrong"
    tampered_path = tmp_path / "tampered.json"
    tampered_path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="visible question hash mismatch"):
        evaluate_research_gold_benchmark(
            [_runtime_result()],
            research_evaluation_summary=_research_summary(),
            benchmark_manifest_path=tampered_path,
            out_dir=tmp_path / "out",
            run_harness=_passing_harness,
        )


def test_gold_manifest_hash_binds_explicit_model_visible_task_intent(
    tmp_path: Path,
) -> None:
    task_intent = {
        "theory": "required",
        "scientific_code": "not_applicable",
        "empirical": "not_applicable",
        "formal": "not_applicable",
    }
    visible_question = {**VISIBLE_QUESTION, "task_intent": task_intent}
    visible_path = tmp_path / "visible-questions.json"
    visible_path.write_text(
        json.dumps({"questions": [visible_question]}),
        encoding="utf-8",
    )
    manifest = json.loads(GOLD_MANIFEST.read_text())
    manifest["model_visible_questions_path"] = str(visible_path)
    manifest["model_visible_questions_sha256"] = _fixture_sha256(visible_path)
    task = manifest["active_tasks"][0]
    task["task_intent"] = dict(task_intent)
    task["visible_question_hash"] = stable_hash(
        {
            key: visible_question[key]
            for key in ("id", "title", "description", "tags", "task_intent")
        }
    )
    path = tmp_path / "task-intent-bound-gold.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    descriptor = validate_research_gold_benchmark_manifest(path)
    assert descriptor["active_task_ids"] == [QUESTION_ID]

    manifest["active_tasks"][0]["task_intent"]["formal"] = "optional"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(
        ValueError,
        match="task_intent does not match the model-visible question",
    ):
        validate_research_gold_benchmark_manifest(path)


def test_gold_evaluator_rejects_runtime_task_intent_drift(
    tmp_path: Path,
) -> None:
    task_intent = {
        "theory": "required",
        "scientific_code": "required",
        "empirical": "required",
        "formal": "not_applicable",
    }
    visible_question = {**VISIBLE_QUESTION, "task_intent": task_intent}
    visible_path = tmp_path / "visible-questions.json"
    visible_path.write_text(
        json.dumps({"questions": [visible_question]}),
        encoding="utf-8",
    )
    manifest = json.loads(GOLD_MANIFEST.read_text())
    manifest["model_visible_questions_path"] = str(visible_path)
    manifest["model_visible_questions_sha256"] = _fixture_sha256(visible_path)
    manifest["active_tasks"][0]["task_intent"] = dict(task_intent)
    manifest["active_tasks"][0]["visible_question_hash"] = stable_hash(
        {
            key: visible_question[key]
            for key in ("id", "title", "description", "tags", "task_intent")
        }
    )
    manifest_path = tmp_path / "task-intent-bound-gold.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    runtime_result = _runtime_result()
    runtime_result["blackboard"]["artifacts"][
        f"runtime_question_metadata:{QUESTION_ID}"
    ]["question"] = {
        **visible_question,
        "task_intent": {**task_intent, "formal": "optional"},
    }

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(),
        benchmark_manifest_path=manifest_path,
        out_dir=tmp_path / "out",
        run_harness=_passing_harness,
    )

    task = result["tasks"][0]
    assert task["task_passed"] is False
    assert task["failure_reasons"] == [
        "runtime-visible question hash does not match the frozen gold task"
    ]


def test_gold_evaluator_does_not_rescore_a_run_from_an_older_question(
    tmp_path: Path,
) -> None:
    runtime_result = _runtime_result()
    runtime_result["blackboard"]["artifacts"][
        f"runtime_question_metadata:{QUESTION_ID}"
    ]["question"] = {
        **VISIBLE_QUESTION,
        "description": "an older benchmark statement",
    }

    result = evaluate_research_gold_benchmark(
        [runtime_result],
        research_evaluation_summary=_research_summary(),
        benchmark_manifest_path=GOLD_MANIFEST,
        out_dir=tmp_path,
        run_harness=_passing_harness,
    )

    task = result["tasks"][0]
    assert task["hidden_harness_execution_attempted"] is False
    assert task["task_passed"] is False
    assert task["failure_reasons"] == [
        "runtime-visible question hash does not match the frozen gold task"
    ]


def _schema_v2_gold_manifest(
    tmp_path: Path,
    *,
    include_empirical: bool = False,
) -> Path:
    contract = {
        "schema_version": 1,
        "estimator_id": "est_ols_hc0_covariance",
        "entrypoint": "run_estimator",
        "request_fields": [
            {
                "clause_id": "request.design_and_outcome",
                "name": "design_and_outcome",
                "meaning": "One regression design matrix and outcome vector.",
                "json_type": "object",
                "shape": "X is n by p and y has length n",
                "units": "as supplied by the benchmark DGP",
                "indexing": "rows are observations and columns are regressors",
                "edge_cases": "Reject nonfinite or dimension-mismatched inputs.",
                "binding": "per_replicate_data",
            }
        ],
        "response_fields": [
            {
                "clause_id": "response.covariance",
                "name": "covariance",
                "meaning": "HC0 covariance estimate for the coefficient vector.",
                "json_type": "array[array[number]]",
                "shape": "p by p",
                "units": "coefficient units squared",
                "indexing": "coefficient order matches design columns",
                "edge_cases": "Every entry must be JSON-finite.",
                "normalization": "finite-sample covariance scale, not n times covariance",
            }
        ],
        "invariants": [
            {
                "clause_id": "invariant.symmetric",
                "meaning": "The returned covariance matrix is symmetric.",
            }
        ],
        "empirical_claims": [
            {
                "clause_id": "claim.empirical.covariance_behavior",
                "meaning": "The frozen empirical assessment checks the stated covariance behavior with Monte Carlo uncertainty.",
            }
        ],
    }
    manifest = json.loads(GOLD_MANIFEST.read_text(encoding="utf-8"))
    visible_question = {
        **VISIBLE_QUESTION,
        "task_intent": dict(manifest["active_tasks"][0]["task_intent"]),
        "estimator_execution_contract": contract,
    }
    visible_path = tmp_path / "schema-v2-visible.json"
    visible_path.write_text(
        json.dumps({"questions": [visible_question]}),
        encoding="utf-8",
    )
    manifest["schema_version"] = 2
    manifest["model_visible_questions_path"] = str(visible_path)
    manifest["model_visible_questions_sha256"] = _fixture_sha256(visible_path)
    task = manifest["active_tasks"][0]
    task["visible_question_hash"] = stable_hash(
        {
            key: visible_question[key]
            for key in (
                "id",
                "title",
                "description",
                "tags",
                "task_intent",
                "estimator_execution_contract",
            )
        }
    )
    task["estimator_execution_contract_id"] = (
        frozen_estimator_execution_contract_id(contract)
    )
    if include_empirical:
        task["hidden_empirical_evaluator"] = deepcopy(
            task["hidden_algorithm_evaluator"]
        )
    for check in task["hidden_algorithm_evaluator"]["acceptance_checks"]:
        check["contract_clause_refs"] = [
            "request.design_and_outcome",
            "response.covariance",
            "invariant.symmetric",
        ]
    if include_empirical:
        for check in task["hidden_empirical_evaluator"]["acceptance_checks"]:
            check["contract_clause_refs"] = [
                "response.covariance",
                "claim.empirical.covariance_behavior",
            ]
    manifest_path = tmp_path / "schema-v2-gold.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _schema_v3_gold_manifest(
    tmp_path: Path,
    *,
    include_empirical: bool = False,
) -> Path:
    path = _schema_v2_gold_manifest(
        tmp_path,
        include_empirical=include_empirical,
    )
    harness = tmp_path / "activation-candidate-harness.py"
    harness.write_text(
        """def run_sandbox(seed, replicates, estimators):
    del seed, replicates
    result = estimators[\"est_ols_hc0_covariance\"]({})
    passed = result.get(\"covariance\") == [[4.0]]
    return {
        \"hidden_cases_passed\": 4 if passed else 0,
        \"all_outputs_finite\": passed,
    }
""",
        encoding="utf-8",
    )
    reference = tmp_path / "activation-reference.py"
    reference.write_text(
        "def run_estimator(request):\n"
        "    del request\n"
        "    return {'covariance': [[4.0]]}\n",
        encoding="utf-8",
    )
    negative = tmp_path / "activation-negative.py"
    negative.write_text(
        "def run_estimator(request):\n"
        "    del request\n"
        "    return {'covariance': [[3.0]]}\n",
        encoding="utf-8",
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 3
    task = manifest["active_tasks"][0]
    evaluator_names = ["hidden_algorithm_evaluator"]
    if include_empirical:
        evaluator_names.append("hidden_empirical_evaluator")
    for name in evaluator_names:
        task[name]["harness_path"] = str(harness)
        task[name]["harness_sha256"] = _fixture_sha256(harness)
        task[name]["dependencies"] = []
    targets = ["algorithm"] + (["empirical"] if include_empirical else [])
    task["activation_candidate_suite"] = {
        "reference_candidate": {
            "estimator_id": "est_ols_hc0_covariance",
            "source_path": str(reference),
            "source_sha256": _fixture_sha256(reference),
            "language": "python",
            "dependencies": [],
        },
        "negative_candidates": [
            {
                "estimator_id": "est_ols_hc0_covariance",
                "source_path": str(negative),
                "source_sha256": _fixture_sha256(negative),
                "language": "python",
                "dependencies": [],
                "must_fail_evaluators": targets,
            }
        ],
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _schema_v4_gold_manifest(tmp_path: Path) -> Path:
    path = _add_semantic_theory_evaluator(
        _schema_v3_gold_manifest(tmp_path),
        tmp_path,
    )
    near_miss = tmp_path / "candidate-mode-long-form-near-miss.md"
    near_miss.write_text(
        "# Near miss\n\n"
        "The requested headline conclusion is stated. A load-bearing intermediate "
        "equality contradicts the definitions, so the endorsed derivation is false.\n",
        encoding="utf-8",
    )
    negative_cases = tmp_path / "candidate-mode-negative-cases.json"
    negative_cases.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "operator-private-long-form-near-miss",
                        "expected_status": "FAIL",
                        "documents": [
                            {
                                "document_id": "near-miss.md",
                                "source_path": str(near_miss),
                                "sha256": _fixture_sha256(near_miss),
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 4
    semantic = manifest["active_tasks"][0]["hidden_theory_semantic_evaluator"]
    semantic["candidate_mode_negative_cases_path"] = str(negative_cases)
    semantic["candidate_mode_negative_cases_sha256"] = _fixture_sha256(
        negative_cases
    )
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_schema_v3_activation_runs_reference_and_negative_through_same_validators(
    tmp_path: Path,
) -> None:
    descriptor = validate_research_gold_benchmark_activation(
        _schema_v3_gold_manifest(tmp_path, include_empirical=True)
    )

    assert descriptor["activation_schema_version"] == 3
    assert descriptor["activation_candidate_validator_path"] == (
        "same_hidden_evaluator_path"
    )
    assert descriptor["activation_reference_tasks_passed"] == 1
    assert descriptor["activation_negative_controls_rejected"] == 2
    serialized = json.dumps(descriptor)
    assert "source_path" not in serialized
    assert "acceptance_checks" not in serialized


def _freeze_synthetic_mechanical_activation(path: Path, tmp_path: Path) -> tuple[Path, Path]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    task = manifest["active_tasks"][0]
    inputs = tmp_path / "frozen-mechanical-inputs.json"
    inputs.write_text(json.dumps(manifest), encoding="utf-8")
    evaluators = {name: task[field] for name, field in (
        ("algorithm", "hidden_algorithm_evaluator"), ("empirical", "hidden_empirical_evaluator"),
    ) if task.get(field)}
    record_path = tmp_path / "frozen-mechanical-record.json"
    record_path.write_text(json.dumps({
        "status": "PASSED_BEFORE_FIRST_PRODUCT_MODEL_CALL",
        "task_id_hash": stable_hash(str(task["task_id"])),
        "reference_validator_hashes": {name: stable_hash(value) for name, value in evaluators.items()},
        "reference_result_hashes": {name: stable_hash({"synthetic": name}) for name in evaluators},
        "negative_controls_rejected": sum(len(row["must_fail_evaluators"])
                                           for row in task["activation_candidate_suite"]["negative_candidates"]),
    }), encoding="utf-8")
    task["mechanical_activation_record"] = {
        "record_path": str(record_path), "record_sha256": _fixture_sha256(record_path),
        "input_manifest_path": str(inputs), "input_manifest_sha256": _fixture_sha256(inputs),
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return record_path, inputs


def test_product_preflight_reads_mechanical_qualification_without_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _schema_v3_gold_manifest(tmp_path, include_empirical=True)
    records = _freeze_synthetic_mechanical_activation(path, tmp_path)
    originals = [record.read_bytes() for record in records]

    def cannot_execute(*_args, **_kwargs):
        raise AssertionError("frozen activation must never execute controls again")

    monkeypatch.setattr(gold_evaluation_module, "_run_activation_candidate_suite", cannot_execute)
    result = validate_research_gold_benchmark_activation(path, require_prequalified_activation=True)
    assert result["activation_reference_tasks_passed"] == 1
    assert result["activation_negative_controls_rejected"] == 2
    assert result["activation_semantic_model_calls"] == 0
    assert "reference_result_hashes" not in json.dumps(result)
    assert [record.read_bytes() for record in records] == originals
    assert validate_research_gold_benchmark_activation(path) == result


@pytest.mark.parametrize("change, message", [
    ("missing", "mechanical activation is not frozen"),
    ("present_empty", "record hash mismatch"),
    ("record_hash", "record hash mismatch"),
    ("input_hash", "input_manifest hash mismatch"),
    ("evaluator", "inputs changed"),
    ("candidate", "inputs changed"),
    ("rejections", "qualification mismatch"),
    ("status", "qualification mismatch"),
    ("result", "reference results missing"),
    ("input_shape", "tasks must be an array"),
])
def test_product_preflight_rejects_changed_or_missing_mechanical_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str, message: str,
) -> None:
    path = _schema_v3_gold_manifest(tmp_path, include_empirical=True)
    record_path, inputs = _freeze_synthetic_mechanical_activation(path, tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    task = manifest["active_tasks"][0]
    reference = task["mechanical_activation_record"]
    if change == "missing":
        task.pop("mechanical_activation_record")
    elif change == "present_empty":
        task["mechanical_activation_record"] = {}
    elif change in {"record_hash", "input_hash"}:
        reference["record_sha256" if change == "record_hash" else "input_manifest_sha256"] = "0" * 64
    elif change == "evaluator":
        task["hidden_algorithm_evaluator"]["seed"] += 1
    elif change == "candidate":
        candidate = task["activation_candidate_suite"]["reference_candidate"]
        source = Path(candidate["source_path"])
        source.write_text(source.read_text(encoding="utf-8") + "\n# changed synthetic input\n", encoding="utf-8")
        candidate["source_sha256"] = _fixture_sha256(source)
    elif change == "input_shape":
        payload = json.loads(inputs.read_text(encoding="utf-8"))
        payload["active_tasks"] = None
        inputs.write_text(json.dumps(payload), encoding="utf-8")
        reference["input_manifest_sha256"] = _fixture_sha256(inputs)
    else:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        key, value = {"rejections": ("negative_controls_rejected", 0),
                      "status": ("status", "FAILED"),
                      "result": ("reference_result_hashes", {})}[change]
        record[key] = value
        record_path.write_text(json.dumps(record), encoding="utf-8")
        reference["record_sha256"] = _fixture_sha256(record_path)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    frozen_record = record_path.read_bytes()

    def cannot_execute(*_args, **_kwargs):
        raise AssertionError("missing or stale authority cannot trigger requalification")

    monkeypatch.setattr(gold_evaluation_module, "_run_activation_candidate_suite", cannot_execute)
    with pytest.raises(ValueError, match=message):
        validate_research_gold_benchmark_activation(
            path, require_prequalified_activation=change != "present_empty",
        )
    assert record_path.read_bytes() == frozen_record


def test_schema_v4_activation_runs_long_form_negative_through_candidate_mode(
    tmp_path: Path,
) -> None:
    path = _schema_v4_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    visible_question = json.loads(
        Path(manifest["model_visible_questions_path"]).read_text(encoding="utf-8")
    )["questions"][0]

    def semantic_runner(**kwargs) -> dict:
        assert kwargs["model"] == "claude-haiku-4-5-20251001"
        assert kwargs["model_tier"] == "haiku"
        assert kwargs["candidate_documents"][0]["content"].startswith(
            "# Reference"
        )
        negatives = kwargs["candidate_mode_negative_cases"]
        assert len(negatives) == 1
        assert negatives[0]["expected_status"] == "FAIL"
        assert negatives[0]["documents"][0]["path"] == "near-miss.md"
        assert "load-bearing intermediate" in negatives[0]["documents"][0][
            "content"
        ]
        return {
            "judgment_hash": "candidate-mode-activation-result",
            "semantic_judge_calibrated": True,
            "candidate_status": "PASS",
            "candidate_document_status": "PASS",
            "n_candidate_mode_negative_cases": 1,
            "n_candidate_mode_negative_cases_correct": 1,
            "candidate_mode_negative_controls_passed": True,
            "n_model_calls": 3,
            "passed": True,
        }

    descriptor = validate_research_gold_benchmark_activation(
        path,
        visible_questions={QUESTION_ID: visible_question},
        run_theory_semantic_judge=semantic_runner,
    )

    assert descriptor["activation_schema_version"] == 4
    assert descriptor["activation_reference_tasks_passed"] == 1
    assert descriptor["activation_negative_controls_rejected"] == 1
    assert descriptor["activation_semantic_reference_documents_passed"] == 1
    assert (
        descriptor[
            "activation_semantic_candidate_mode_negative_controls_rejected"
        ]
        == 1
    )
    assert descriptor["activation_semantic_model_calls"] == 3
    serialized = json.dumps(descriptor)
    assert "operator-private-long-form-near-miss" not in serialized
    assert "load-bearing intermediate" not in serialized


def test_product_runtime_requires_frozen_schema_v4_semantic_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _schema_v4_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    visible_question = json.loads(
        Path(manifest["model_visible_questions_path"]).read_text(encoding="utf-8")
    )["questions"][0]
    semantic_calls = 0

    def semantic_runner(**_kwargs) -> dict:
        nonlocal semantic_calls
        semantic_calls += 1
        raise AssertionError("product preflight must not qualify the semantic judge")

    def mechanical_runner(*_args, **_kwargs) -> dict:
        raise AssertionError("product preflight must reject before mechanical execution")

    monkeypatch.setattr(
        gold_evaluation_module,
        "_run_activation_candidate_suite",
        mechanical_runner,
    )
    with pytest.raises(
        ValueError,
        match="semantic activation is not frozen",
    ):
        validate_research_gold_benchmark_activation(
            path,
            visible_questions={QUESTION_ID: visible_question},
            run_theory_semantic_judge=semantic_runner,
            require_prequalified_activation=True,
        )

    assert semantic_calls == 0


def test_schema_v4_activation_fails_when_candidate_mode_negative_is_accepted(
    tmp_path: Path,
) -> None:
    path = _schema_v4_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    visible_question = json.loads(
        Path(manifest["model_visible_questions_path"]).read_text(encoding="utf-8")
    )["questions"][0]

    def semantic_runner(**kwargs) -> dict:
        del kwargs
        return {
            "semantic_judge_calibrated": False,
            "candidate_status": "PASS",
            "candidate_document_status": "PASS",
            "n_candidate_mode_negative_cases": 1,
            "n_candidate_mode_negative_cases_correct": 0,
            "candidate_mode_negative_controls_passed": False,
            "n_model_calls": 3,
            "passed": False,
        }

    with pytest.raises(
        ValueError,
        match="candidate-mode negative control failed exact candidate adjudication",
    ) as exc_info:
        validate_research_gold_benchmark_activation(
            path,
            visible_questions={QUESTION_ID: visible_question},
            run_theory_semantic_judge=semantic_runner,
        )
    assert "candidate_mode_negative=0/1" in str(exc_info.value)
    assert "reference_status=PASS" in str(exc_info.value)
    assert "calibrated=False" in str(exc_info.value)


def test_schema_v4_requires_hash_bound_candidate_mode_negative_cases(
    tmp_path: Path,
) -> None:
    path = _schema_v4_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    semantic = manifest["active_tasks"][0]["hidden_theory_semantic_evaluator"]
    semantic.pop("candidate_mode_negative_cases_path")
    semantic.pop("candidate_mode_negative_cases_sha256")
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="candidate-mode negative cases file is missing",
    ):
        validate_research_gold_benchmark_manifest(path)


def test_live_activation_rejects_historical_schema_v2(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires schema_version 3"):
        validate_research_gold_benchmark_activation(
            _schema_v2_gold_manifest(tmp_path)
        )


def test_schema_v3_activation_rejects_reference_candidate_failure(
    tmp_path: Path,
) -> None:
    path = _schema_v3_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    suite = manifest["active_tasks"][0]["activation_candidate_suite"]
    negative = suite["negative_candidates"][0]
    suite["reference_candidate"] = {
        key: value for key, value in negative.items() if key != "must_fail_evaluators"
    }
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="reference failed exact candidate validators"):
        validate_research_gold_benchmark_activation(path)


def test_schema_v3_activation_rejects_vacuous_candidate_validator(
    tmp_path: Path,
) -> None:
    path = _schema_v3_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    evaluator = manifest["active_tasks"][0]["hidden_algorithm_evaluator"]
    harness = Path(evaluator["harness_path"])
    harness.write_text(
        """def run_sandbox(seed, replicates, estimators):
    del seed, replicates
    estimators[\"est_ols_hc0_covariance\"]({})
    return {\"hidden_cases_passed\": 4, \"all_outputs_finite\": True}
""",
        encoding="utf-8",
    )
    evaluator["harness_sha256"] = _fixture_sha256(harness)
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="negative control 0 was not rejected"):
        validate_research_gold_benchmark_activation(path)


def test_schema_v3_requires_hidden_checks_to_cover_every_public_clause(
    tmp_path: Path,
) -> None:
    path = _schema_v3_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    checks = manifest["active_tasks"][0]["hidden_algorithm_evaluator"][
        "acceptance_checks"
    ]
    for check in checks:
        check["contract_clause_refs"] = ["response.covariance"]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="does not exercise public contract clauses"):
        validate_research_gold_benchmark_activation(path)


def test_schema_v2_gold_binds_hidden_checks_to_visible_contract_clauses(
    tmp_path: Path,
) -> None:
    path = _schema_v2_gold_manifest(tmp_path, include_empirical=True)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    visible = json.loads(
        Path(manifest["model_visible_questions_path"]).read_text(
            encoding="utf-8"
        )
    )
    contract = visible["questions"][0]["estimator_execution_contract"]
    descriptor = validate_research_gold_benchmark_manifest(path)

    assert descriptor["estimator_execution_contract_ids"] == {
        QUESTION_ID: frozen_estimator_execution_contract_id(contract)
    }
    assert descriptor["estimator_execution_contract_ids"][QUESTION_ID].startswith(
        "frozen_estimator_execution_contract:"
    )


def test_schema_v2_gold_rejects_ambiguous_visible_field_semantics(
    tmp_path: Path,
) -> None:
    path = _schema_v2_gold_manifest(tmp_path, include_empirical=True)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    visible_path = Path(manifest["model_visible_questions_path"])
    visible = json.loads(visible_path.read_text(encoding="utf-8"))
    question = visible["questions"][0]
    question["estimator_execution_contract"]["response_fields"][0][
        "meaning"
    ] = ""
    visible_path.write_text(json.dumps(visible), encoding="utf-8")
    manifest["model_visible_questions_sha256"] = _fixture_sha256(visible_path)
    task = manifest["active_tasks"][0]
    task["visible_question_hash"] = stable_hash(
        {
            key: question[key]
            for key in (
                "id",
                "title",
                "description",
                "tags",
                "task_intent",
                "estimator_execution_contract",
            )
        }
    )
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="missing meaning"):
        validate_research_gold_benchmark_manifest(path)


def test_schema_v2_gold_requires_visible_contract_for_scientific_code(
    tmp_path: Path,
) -> None:
    manifest = json.loads(GOLD_MANIFEST.read_text(encoding="utf-8"))
    manifest["schema_version"] = 2
    path = tmp_path / "schema-v2-missing-contract.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="estimator_execution_contract is required"):
        validate_research_gold_benchmark_manifest(path)


def test_schema_v2_gold_rejects_unknown_contract_clause_reference(
    tmp_path: Path,
) -> None:
    path = _schema_v2_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["active_tasks"][0]["hidden_algorithm_evaluator"][
        "acceptance_checks"
    ][0]["contract_clause_refs"] = ["response.unstated_semantics"]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown model-visible contract clauses"):
        validate_research_gold_benchmark_manifest(path)


def test_schema_v2_gold_rejects_evaluator_estimator_identity_drift(
    tmp_path: Path,
) -> None:
    path = _schema_v2_gold_manifest(tmp_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["active_tasks"][0]["hidden_algorithm_evaluator"][
        "required_estimator_id"
    ] = "est_other"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="model-visible contract"):
        validate_research_gold_benchmark_manifest(path)


def test_schema_v2_gold_requires_public_empirical_claim(
    tmp_path: Path,
) -> None:
    path = _schema_v2_gold_manifest(tmp_path, include_empirical=True)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    visible_path = Path(manifest["model_visible_questions_path"])
    visible = json.loads(visible_path.read_text(encoding="utf-8"))
    question = visible["questions"][0]
    question["estimator_execution_contract"]["empirical_claims"] = []
    visible_path.write_text(json.dumps(visible), encoding="utf-8")
    manifest["model_visible_questions_sha256"] = _fixture_sha256(visible_path)
    task = manifest["active_tasks"][0]
    task["visible_question_hash"] = stable_hash(
        {
            key: question[key]
            for key in (
                "id",
                "title",
                "description",
                "tags",
                "task_intent",
                "estimator_execution_contract",
            )
        }
    )
    task["estimator_execution_contract_id"] = (
        frozen_estimator_execution_contract_id(
            question["estimator_execution_contract"]
        )
    )
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="requires an empirical claim"):
        validate_research_gold_benchmark_manifest(path)


def test_schema_v2_empirical_check_must_cite_public_empirical_claim(
    tmp_path: Path,
) -> None:
    path = _schema_v2_gold_manifest(tmp_path, include_empirical=True)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["active_tasks"][0]["hidden_empirical_evaluator"][
        "acceptance_checks"
    ][0]["contract_clause_refs"] = ["response.covariance"]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="must cite a model-visible empirical claim"):
        validate_research_gold_benchmark_manifest(path)
