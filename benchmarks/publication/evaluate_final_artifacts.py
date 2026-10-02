"""Prospective common publication outcomes, not a product research controller.

The trusted study runner collects a terminated run through its existing final
submission reader and supplies only that selection's immutable material here.
It owns collection, exact-input projection and prospective authority qualification.
No internal ACCEPT verdict or isolated product-review receipt is required.
"""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ai_statistician.fingerprint import stable_hash
from ai_statistician.client_tool_loop import read_hash_bound_utf8_file
from ai_statistician.research_gold_evaluation import (
    _exact_formal_kernel_authority,
    _hidden_evaluator_validation_errors,
    _hidden_execution_summary,
    _project_path,
    _run_hidden_artifact_harness,
    _run_hidden_document_semantic_evaluation,
    _visible_question_hash_payload,
)
from ai_statistician.research_schema import (
    OpenResearchQuestion, research_dimension_requirements, research_question_payload,
    research_task_intent_requirement,
)
from ai_statistician.scientific_project import scientific_project_hash
from ai_statistician.scientific_sandbox import ScientificEstimatorBinding, execute_scientific_sandbox
from ai_statistician.theory_workspace import load_theory_workspace_documents


def publication_material_from_submission(
    submission: Mapping[str, Any], *, source_kind: str,
    control_estimator_scopes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Project a trusted final reader's selected product/control material.

    This is the fixed evaluator view for the current production-backed comparison
    arms, not a native-file decoder or a substitute for either final reader.
    The study fixes control scope/estimator identities before inference. Missing
    selections stay missing; exploration is never relabelled as confirmation.
    Source replication uses the selected checkpoint's exact report and execution
    files. It does not require a Critic or theory receipt for a source-only task.
    Formal closures require their own prospective selection.
    """

    submission = deepcopy(dict(submission))
    empirical_metadata = {}
    source_checkpoint = {}
    if source_kind == "runtime":
        if control_estimator_scopes is not None:
            raise ValueError("runtime projection does not take control scope identities")
        payloads = submission["selected_artifacts"]
        source_checkpoint = payloads.get("source_replication", {})
        core = payloads.get("theory", {})
        source_rows = payloads.get("scientific_code", {}).get("prototypes", [])
        experiment = payloads.get("empirical", {})
        empirical_rows = experiment.get("generated_simulation_sandbox_prototypes", [])
        empirical_metadata = {key: experiment[key] for key in (
            "empirical_evaluation_phase", "evaluator_source_confirmation", "confirmatory_empirical_evidence_eligible"
        ) if key in experiment}
    elif source_kind == "control":
        if control_estimator_scopes is None:
            raise ValueError("control projection requires its frozen estimator scopes")
        if (any(not scope or not estimator for scope, estimator in control_estimator_scopes.items())
            or len(set(control_estimator_scopes.values())) != len(control_estimator_scopes)):
            raise ValueError("control projection requires unique estimator identities")
        payloads = submission["checkpoint_payloads"]
        theory_payload = payloads.get("theory", {})
        core = theory_payload.get("core_packet", {})
        if core.get("artifact_kind") == "SourceReplicationCheckpoint":
            source_checkpoint, core = core, {}
        else:
            source_checkpoint = theory_payload.get("source_replication_checkpoint", {})
        source_rows = []
        for scope, payload in payloads.items():
            if scope in {"simulation", "confirmation"} or "code_draft" not in payload:
                continue
            if scope not in control_estimator_scopes:
                raise ValueError("selected control source is outside the frozen scope contract")
            draft, row = payload["code_draft"], payload["check_result"]["prototype"]
            expected_id = control_estimator_scopes[scope]
            if (row.get("estimator_id") != expected_id or row.get("source_code") != draft["code"]
                or row.get("language") != draft["language"] or row.get("dependencies", []) != draft["dependencies"]
                or row.get("project_hash") != scientific_project_hash(
                    language=draft["language"], code=draft["code"], project_files=draft.get("project_files", []))):
                raise ValueError("selected control draft differs from its source record")
            source_rows.append(row)
        empirical_rows = [payloads[scope]["check_result"]["prototype"]
                          for scope in ("simulation", "confirmation") if scope in payloads]
    else:
        raise ValueError("publication projection requires an explicit supported source kind")
    bindings = []
    for row in source_rows:
        binding = ScientificEstimatorBinding(
            artifact_id=row["estimator_id"], language=row["language"], code=row["source_code"],
            code_hash=row["script_hash"], dependencies=tuple(row.get("dependencies", [])),
            project_files=tuple(row.get("project_files", [])), project_hash=row["project_hash"],
        )
        if (binding.code_hash != stable_hash(binding.code) or binding.project_hash != scientific_project_hash(
            language=binding.language, code=binding.code, project_files=binding.project_files)):
            raise ValueError("selected source record has invalid immutable identity")
        bindings.append(binding)
    documents = [{"path": path, "content": content, "sha256": hashlib.sha256(content.encode()).hexdigest()}
                 for path, content in load_theory_workspace_documents(core).items()]
    return {"theory_documents": documents, "estimator_bindings": tuple(bindings),
            "empirical_artifact": {"generated_simulation_rows": deepcopy(empirical_rows), **empirical_metadata} if empirical_rows else None,
            **({"source_replication_artifact": _selected_source_replication_material(source_checkpoint, submission)}
               if source_checkpoint else {})}


def _selected_source_replication_material(checkpoint, submission):
    """Read the actual selection's immutable files; never search for another run."""

    body = deepcopy(dict(checkpoint))
    for field in ("workspace_evidence_id", "workspace_evidence_hash", "runtime_completion_status", "boundary"):
        body.pop(field, None)
    checkpoint_id = body.pop("checkpoint_id", None)
    if (checkpoint_id != "source_replication_checkpoint:" + stable_hash(body)[:20]
        or body.get("artifact_kind") != "SourceReplicationCheckpoint"
        or body.get("question_id") != submission["question_id"] or body.get("task_intent") != submission["task_intent"]):
        raise ValueError("selected source checkpoint identity mismatch")
    report_ref = body["report_document"]
    report, errors = read_hash_bound_utf8_file(report_ref)
    if errors:
        raise ValueError("selected source report identity mismatch: " + ",".join(errors))

    def read_execution(ref):
        text, errors = read_hash_bound_utf8_file(ref)
        if errors:
            raise ValueError("selected source execution file identity mismatch: " + ",".join(errors))
        manifest = json.loads(text)
        unsigned = dict(manifest)
        manifest_hash = unsigned.pop("manifest_hash", None)
        if (manifest_hash != stable_hash(unsigned) or manifest.get("question_id") != submission["question_id"]
            or manifest.get("artifact_kind") != "SourceReplicationManifest"
            or any(manifest.get(key) != ref.get(key) for key in ("artifact_id", "manifest_hash", "execution_status"))):
            raise ValueError("selected source execution manifest identity mismatch")
        return manifest

    selected = read_execution(body["source_replication_manifest_ref"])
    attempts = [read_execution(ref) for ref in body.get("source_execution_attempt_refs", [])]
    if attempts:
        selected_run = body["selected_source_run"]
        if (type(selected_run) is not int or not 1 <= selected_run <= len(attempts)
            or attempts[selected_run - 1] != selected
            or any(ref.get("source_run") != index for index, ref in enumerate(body["source_execution_attempt_refs"], 1))):
            raise ValueError("selected source attempt lineage mismatch")
    return {"checkpoint_id": checkpoint_id,
            "report_document": {"path": report_ref["relative_path"], "content": report, "sha256": report_ref["sha256"]},
            "source_execution": selected, "source_execution_attempts": attempts,
            "unresolved_gaps": deepcopy(body["unresolved_gaps"])}


def evaluate_final_research_artifacts(
    *, question: OpenResearchQuestion, task: Mapping[str, Any],
    submission_identity: Mapping[str, Any], project_root: Path, out_dir: Path,
    theory_documents: Sequence[Mapping[str, Any]] = (),
    estimator_bindings: Sequence[ScientificEstimatorBinding] = (),
    empirical_artifact: Mapping[str, Any] | None = None,
    source_replication_artifact: Mapping[str, Any] | None = None,
    formal_artifacts: Mapping[str, Any] | None = None,
    theory_semantic_judge_provider: Any = None,
    run_theory_semantic_judge: Any = None,
) -> dict[str, Any]:
    """Judge exact final material against one prospectively frozen task authority.

    Theory uses the existing separately prequalified document-review protocol.
    Scientific code uses held evaluator data and exact estimator bindings.
    Empirical/replication evaluators inspect submitted material via evaluate_artifact;
    they do not manufacture a missing candidate experiment by rerunning its method.
    Their specific scientific checks and calibration belong to the frozen study.
    Artifact evaluators take a JSON view fixed before the study. Binary snapshots
    remain with the collector; this function does not decode or discard them.
    Do not use this entry to reevaluate any consumed legacy task or qualification.
    """

    public = deepcopy(research_question_payload(question, include_task_intent=True))
    task = deepcopy(dict(task))
    submission_identity_hash = stable_hash(deepcopy(dict(submission_identity)))
    intent = public.get("task_intent", {})
    if (task.get("task_id") != question.id or task.get("task_intent") != intent
        or task.get("visible_question_hash") != stable_hash(_visible_question_hash_payload(public))
        or submission_identity.get("question_id") != question.id
        or submission_identity.get("question_hash") != stable_hash(public)
        or submission_identity.get("task_intent") != intent):
        raise ValueError("publication authority/submission differs from the frozen question")
    requirements = research_dimension_requirements(intent)
    requirements.update({dimension: research_task_intent_requirement(intent, dimension)
                         for dimension in intent if dimension not in requirements})
    documents = deepcopy(list(theory_documents))
    bindings = deepcopy(tuple(estimator_bindings))
    empirical, replication, formal = deepcopy((empirical_artifact, source_replication_artifact, formal_artifacts))
    if (any(not row.artifact_id for row in bindings) or len({row.artifact_id for row in bindings}) != len(bindings)
        or any(row.code_hash != stable_hash(row.code) or row.project_hash != scientific_project_hash(
            language=row.language, code=row.code, project_files=row.project_files) for row in bindings)):
        raise ValueError("publication source binding identity mismatch")
    if any(not row.get("path") or not isinstance(row.get("content"), str)
           or hashlib.sha256(row["content"].encode()).hexdigest() != row.get("sha256") for row in documents):
        raise ValueError("publication theory document identity mismatch")
    if len({row["path"] for row in documents}) != len(documents):
        raise ValueError("publication theory document paths repeat")
    evaluators = {dimension: task.get(field, {}) for dimension, field in (
        ("theory", "hidden_theory_evaluator"), ("scientific_code", "hidden_algorithm_evaluator"),
        ("empirical", "hidden_empirical_evaluator"), ("source_replication", "hidden_source_replication_evaluator"))}
    harness_sources = {}
    for dimension, evaluator in evaluators.items():
        if not evaluator:
            continue
        errors = _hidden_evaluator_validation_errors(
            evaluator, task_index=0, label=dimension, project_root=project_root,
            require_estimator=dimension == "scientific_code", allowed_contract_clause_ids=None,
        )
        if dimension != "scientific_code" and evaluator.get("language") != "python":
            errors.append("artifact evaluator must use the existing Python evaluate_artifact ABI")
        if errors:
            raise ValueError("; ".join(errors))
        raw = _project_path(str(evaluator["harness_path"]), project_root=project_root).read_bytes()
        if hashlib.sha256(raw).hexdigest() != evaluator["harness_sha256"]:
            raise ValueError("publication evaluator source changed during validation")
        harness_sources[dimension] = raw.decode("utf-8")
    semantic = task.get("hidden_theory_semantic_evaluator", {})
    if semantic and semantic.get("provider") != "local":
        raise ValueError("publication model evaluation requires the frozen local open-weight provider")
    for dimension, candidate in (("empirical", empirical), ("source_replication", replication)):
        if (candidate is not None and evaluators[dimension]
            and requirements.get(dimension, "not_applicable") != "not_applicable"):
            try:
                json.dumps(candidate, allow_nan=False)
            except (TypeError, ValueError) as exc:
                raise ValueError("publication artifact evaluator requires its frozen JSON view") from exc
    out_dir.mkdir(parents=True, exist_ok=False)
    material = {"theory_documents": documents, "estimators": [asdict(row) for row in bindings],
                "empirical": empirical, "source_replication": replication, "formal": formal}
    dimensions = {}
    for dimension, requirement in requirements.items():
        row = {"requirement": requirement, "status": "not_requested"}
        dimensions[dimension] = row
        if requirement == "not_applicable":
            continue
        evaluator = evaluators.get(dimension, {})
        if dimension == "formal":
            if formal is not None:
                passed, errors = _exact_formal_kernel_authority(formal, runtime_question=public)
                row.update(status="passed" if passed else "failed", errors=errors)
            elif requirement == "required":
                row["status"] = "missing"
            continue
        candidate = {"theory": {"documents": documents} if documents else None,
                     "scientific_code": bindings or None, "empirical": empirical,
                     "source_replication": replication}.get(dimension)
        if candidate is None:
            if requirement == "required":
                row["status"] = "missing"
            continue
        if not evaluator and not (dimension == "theory" and semantic):
            row["status"] = "unconfigured"
            continue
        passed = True
        if evaluator:
            harness = harness_sources[dimension]
            execution_options = dict(sandbox_dir=out_dir / dimension, artifact_id="publication-" + dimension,
                                     seed=int(evaluator.get("seed", 0)), replicates=int(evaluator.get("replicates", 1)),
                                     timeout_s=int(evaluator.get("timeout_seconds", 60)))
            if dimension == "scientific_code":
                required_id = str(evaluator["required_estimator_id"])
                if required_id not in {binding.artifact_id for binding in bindings}:
                    row["status"] = "missing"
                    continue
                execution = execute_scientific_sandbox(
                    **execution_options, language=evaluator["language"], code=harness,
                    dependencies=tuple(evaluator.get("dependencies", [])), estimator_bindings=bindings,
                ).to_json()
            else:
                required_id = ""
                execution = _run_hidden_artifact_harness(
                    **execution_options, harness_code=harness, harness_dependencies=tuple(evaluator.get("dependencies", [])),
                    candidate_artifact=candidate,
                )
            summary = _hidden_execution_summary(execution, evaluator=evaluator, required_estimator_id=required_id)
            row["execution"] = summary
            passed = summary["passed"]
        if dimension == "theory":
            # A structural artifact check alone cannot accept a mathematical argument.
            if not semantic:
                row["status"] = "unconfigured"
                continue
            judgment, error = _run_hidden_document_semantic_evaluation(
                evaluator=deepcopy(semantic), task_id=question.id, visible_question=deepcopy(public),
                candidate_documents=deepcopy(documents), project_root=project_root,
                run_semantic_judge=run_theory_semantic_judge,
                semantic_judge_provider=theory_semantic_judge_provider, semantic_artifact_role="theory",
            )
            row["semantic_judgment_hash"] = str((judgment or {}).get("judgment_hash", ""))
            if judgment is not None:
                (out_dir / "theory").mkdir(exist_ok=True)
                (out_dir / "theory" / "semantic_judgment.json").write_text(
                    json.dumps(judgment, indent=2) + "\n", encoding="utf-8")
            if error:
                row["errors"] = [error]
            passed = passed and not error and (judgment or {}).get("passed") is True
        row["status"] = "passed" if passed else "failed"
    required = [row for row in dimensions.values() if row["requirement"] == "required"]
    result = {"question_id": question.id, "question_hash": stable_hash(public), "task_hash": stable_hash(task),
              "submission_identity_hash": submission_identity_hash,
              "submitted_material_hash": stable_hash(material), "dimension_status": dimensions,
              "task_passed": bool(required) and all(row["status"] == "passed" for row in required),
              "internal_acceptance_required": False, "runtime_feedback_generated": False,
              "evaluation_role": "external_publication_outcome_not_product_acceptance_or_proof"}
    (out_dir / "outcome.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
