"""Prospective common publication outcomes, not a product research controller.

The trusted study runner collects a terminated run through its existing final
submission reader and supplies only that selection's immutable material here.
It owns collection, exact-input projection and prospective authority qualification.
No internal ACCEPT verdict or isolated product-review receipt is required.
"""

from copy import deepcopy
from dataclasses import asdict
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
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
from ai_statistician.research_source_library import _source_replication_result_bytes
from ai_statistician.scientific_project import scientific_main_path, scientific_project_hash
from ai_statistician.scientific_sandbox import (
    ScientificEstimatorBinding, execute_scientific_sandbox, normalized_scientific_dependencies,
)
from ai_statistician.theory_workspace import load_theory_workspace_documents


def publication_dimension_requirements(task_intent: Mapping[str, Any]) -> dict[str, str]:
    """Reject active intent dimensions this common outcome cannot assess."""
    requirements = research_dimension_requirements(task_intent)
    requirements.update({dimension: research_task_intent_requirement(task_intent, dimension)
                         for dimension in task_intent if dimension not in requirements})
    unsupported = sorted(dimension for dimension, requirement in requirements.items()
                         if requirement != "not_applicable" and dimension not in {
                             "theory", "scientific_code", "empirical", "formal", "source_replication"})
    if unsupported:
        raise ValueError("publication outcome does not support active dimensions: " + ", ".join(unsupported))
    return requirements


def native_final_artifact_paths(*, workspace_root: Path, artifact_roots: Mapping[str, str]) -> dict[str, list[str]]:
    """Resolve every selected final-tree file after the trusted host terminates.

    The study freezes roots before calls. Authors choose filenames within them;
    this does not search drafts, select a better source or judge completeness.
    Pass the returned lists to the existing native snapshot collector once and
    retain them with the frozen root contract, not a later workspace rescan.
    """
    root = workspace_root.resolve()
    if not root.is_dir() or not artifact_roots:
        raise ValueError("native final collection requires a workspace and explicit artifact roots")
    paths, prefixes = {}, []
    for scope, relative in artifact_roots.items():
        if not isinstance(scope, str) or not scope.strip() or not isinstance(relative, str):
            raise ValueError("native artifact roots require named canonical relative directories")
        prefix = Path(relative)
        if (not relative or not prefix.parts or "\\" in relative or "\x00" in relative
            or prefix.is_absolute() or relative != prefix.as_posix()
            or any(part in {".", ".."} for part in prefix.parts)):
            raise ValueError("native artifact root is not canonical and relative")
        if any(prefix == other or prefix in other.parents or other in prefix.parents for other in prefixes):
            raise ValueError("native artifact roots overlap")
        prefixes.append(prefix)
        if any((root / Path(*prefix.parts[:index])).is_symlink() for index in range(1, len(prefix.parts) + 1)):
            raise ValueError("native artifact root contains a symlink")
        directory = root / prefix
        if directory.exists() and not directory.is_dir():
            raise ValueError("native artifact root is not a directory")
        paths[scope] = []
        for path in sorted(directory.rglob("*")) if directory.is_dir() else ():
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise ValueError("native final tree contains a symlink or unsupported file type")
            if path.is_file():
                paths[scope].append(path.relative_to(root).as_posix())
    return paths


def publication_material_from_submission(
    submission: Mapping[str, Any], *, source_kind: str,
    control_estimator_scopes: Mapping[str, str] | None = None,
    native_estimator_projects: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Project a trusted final reader's selected product/control/native material.

    This is the fixed evaluator view for the current production-backed comparison
    arms, not a substitute for any final reader.
    The study fixes control scope/estimator identities before inference. Missing
    selections stay missing; exploration is never relabelled as confirmation.
    Source replication uses the selected checkpoint's exact report and execution
    files. It does not require a Critic or theory receipt for a source-only task.
    Formal closures require their own prospective selection.
    """

    submission = deepcopy(dict(submission))
    if source_kind == "native":
        if control_estimator_scopes is not None or native_estimator_projects is None:
            raise ValueError("native projection requires only its frozen estimator project contract")
        return _native_publication_material(submission, native_estimator_projects)
    if native_estimator_projects is not None:
        raise ValueError("native estimator projects are only valid for native projection")
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


def _native_publication_material(submission, projects):
    """Decode exact collected files, not author verdicts or best-source guesses.

    Freeze project IDs, roots, languages and dependency metadata before calls.
    Main filenames reuse the existing executor ABI; helpers retain their paths.
    Human assessment also receives the complete native snapshot, including report
    and ancillary files, bound by the supplied submission identity. This view
    supplies no execution, confirmation, source-fidelity or review credit.
    """
    if submission.get("evidence_role") != "submission_not_scientific_acceptance":
        raise ValueError("native projection requires the trusted native snapshot reader")
    files = submission["artifact_bytes"]
    if set(files) != set(submission["artifact_refs"]):
        raise ValueError("native projection differs from its collected scope inventory")
    for scope, rows in files.items():
        refs = submission["artifact_refs"][scope]
        if set(rows) != set(refs):
            raise ValueError("native projection differs from its collected file inventory")
        for path, raw in rows.items():
            if (not isinstance(raw, bytes) or len(raw) != refs[path]["byte_size"]
                or hashlib.sha256(raw).hexdigest() != refs[path]["sha256"]):
                raise ValueError("native projection file identity mismatch: " + path)
    documents = []
    for path, raw in sorted(files.get("theory", {}).items()):
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("native theory source must be UTF-8 Markdown/LaTeX: " + path) from exc
        documents.append({"path": path, "content": content, "sha256": hashlib.sha256(raw).hexdigest()})
    bindings, roots, covered = [], [], set()
    source_files = files.get("scientific_code", {})
    for estimator_id, spec in projects.items():
        if (not isinstance(estimator_id, str) or not estimator_id.strip() or not isinstance(spec, Mapping)
            or set(spec) - {"root", "language", "dependencies"} or spec.get("language") not in {"python", "r"}
            or not isinstance(spec.get("root"), str)):
            raise ValueError("invalid frozen native estimator project contract")
        root, language = PurePosixPath(spec["root"]), spec["language"]
        if (not root.parts or root.is_absolute() or spec["root"] != root.as_posix()
            or "\\" in spec["root"] or "\x00" in spec["root"] or ".." in root.parts
            or any(root == other or root in other.parents or other in root.parents for other in roots)):
            raise ValueError("native estimator project roots must be canonical, relative and disjoint")
        roots.append(root)
        dependencies = normalized_scientific_dependencies(spec.get("dependencies", []), language=language)
        selected = {}
        for path, raw in source_files.items():
            relative = PurePosixPath(path)
            if relative.is_relative_to(root):
                covered.add(path)
                try:
                    selected[relative.relative_to(root).as_posix()] = raw.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ValueError("native estimator project requires UTF-8 source/support files: " + path) from exc
        main = scientific_main_path(language)
        if main not in selected:
            continue
        code = selected.pop(main)
        support = tuple({"path": path, "content": content} for path, content in sorted(selected.items()))
        bindings.append(ScientificEstimatorBinding(estimator_id, language, code, stable_hash(code),
            dependencies=dependencies, project_files=support,
            project_hash=scientific_project_hash(language=language, code=code, project_files=support)))
    if covered != set(source_files):
        raise ValueError("selected native source is outside the frozen estimator project roots")

    def file_view(scope):
        rows = files.get(scope, {})
        if not rows:
            return None
        return {"files": {path: {"base64": base64.b64encode(raw).decode("ascii"),
            "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)} for path, raw in sorted(rows.items())},
            "missing_files": list(submission["missing_artifacts"].get(scope, []))}

    replication = file_view("source_replication")
    if replication is not None:
        replication["host_process"] = deepcopy(submission["host_process"])
    return {"theory_documents": documents, "estimator_bindings": tuple(bindings),
            "empirical_artifact": file_view("empirical"),
            **({"source_replication_artifact": replication} if replication is not None else {})}


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
    files = {}
    results = selected.get("result_artifacts", [])
    for descriptor in (*results, *selected.get("execution_streams", [])):
        path, _, raw = _source_replication_result_bytes(selected, descriptor["relative_path"])
        if len(raw) != descriptor["size_bytes"]:
            raise ValueError("selected source result size differs from its execution record")
        files[path.as_posix()] = {"base64": base64.b64encode(raw).decode("ascii"),
            "sha256": hashlib.sha256(raw).hexdigest(), "byte_size": len(raw)}
    return {"checkpoint_id": checkpoint_id,
            "report_document": {"path": report_ref["relative_path"], "content": report, "sha256": report_ref["sha256"]},
            "source_execution": selected, "source_execution_attempts": attempts,
            "files": files,
            "missing_files": [path for path in selected.get("declared_result_artifact_paths", [])
                              if path not in {row["relative_path"] for row in results}],
            "unresolved_gaps": deepcopy(body["unresolved_gaps"])}


def publication_submitted_material_hash(
    *, theory_documents=(), estimator_bindings=(), empirical_artifact=None,
    source_replication_artifact=None, formal_artifacts=None,
) -> str:
    """Identify the complete evaluator view before independent adjudication.

    This does not validate collection, qualify a reviewer or assess mathematics.
    The trusted caller must project the actual final selection, not another draft.
    """

    return stable_hash({"theory_documents": list(theory_documents),
                        "estimators": [asdict(row) for row in estimator_bindings],
                        "empirical": empirical_artifact, "source_replication": source_replication_artifact,
                        "formal": formal_artifacts})


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
    external_theory_review: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Judge exact final material against one prospectively frozen task authority.

    Theory uses either a prospectively fixed external adjudication authority or
    the existing separately prequalified model protocol, never a verdict fallback.
    External records are supplied by the trusted study caller, not the author.
    Hash validation binds an assessment to material; it cannot certify reviewer
    expertise, independence, honesty or mathematical correctness.
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
    requirements = publication_dimension_requirements(intent)
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
    authority = task.get("external_theory_authority", {})
    review = deepcopy(dict(external_theory_review)) if external_theory_review is not None else None
    material_hash = publication_submitted_material_hash(
        theory_documents=documents, estimator_bindings=bindings, empirical_artifact=empirical,
        source_replication_artifact=replication, formal_artifacts=formal,
    )
    if (authority and semantic) or (review is not None and not authority):
        raise ValueError("publication theory requires one prospectively fixed assessment authority")
    if authority:
        if not isinstance(authority.get("authority_id"), str) or not authority["authority_id"].strip():
            raise ValueError("external theory authority identity is missing")
        protocol, errors = read_hash_bound_utf8_file(authority.get("protocol", {}))
        if errors or not protocol.strip():
            raise ValueError("external theory protocol identity is invalid")
        if review is not None:
            expected = {"authority_id": authority["authority_id"], "task_hash": stable_hash(task),
                        "submission_identity_hash": submission_identity_hash, "submitted_material_hash": material_hash}
            if any(review.get(key) != value for key, value in expected.items()):
                raise ValueError("external theory assessment differs from the final submission or frozen authority")
            if not isinstance(review.get("verdict"), str) or review["verdict"] not in {"accepted", "rejected", "unresolved"}:
                raise ValueError("external theory assessment verdict is invalid")
            report, errors = read_hash_bound_utf8_file(review.get("report", {}))
            if errors or not report.strip():
                raise ValueError("external theory assessment report identity is invalid")
    for dimension, candidate in (("empirical", empirical), ("source_replication", replication)):
        if (candidate is not None and evaluators[dimension]
            and requirements.get(dimension, "not_applicable") != "not_applicable"):
            try:
                json.dumps(candidate, allow_nan=False)
            except (TypeError, ValueError) as exc:
                raise ValueError("publication artifact evaluator requires its frozen JSON view") from exc
    out_dir.mkdir(parents=True, exist_ok=False)
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
        if not evaluator and not (dimension == "theory" and (semantic or authority)):
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
                    execution_profile=evaluator.get("execution_profile", "scientific_wasm"),
                    dependencies=tuple(evaluator.get("dependencies", [])), estimator_bindings=bindings,
                ).to_json()
            else:
                required_id = ""
                execution = _run_hidden_artifact_harness(
                    **execution_options, harness_code=harness, harness_dependencies=tuple(evaluator.get("dependencies", [])),
                    harness_execution_profile=evaluator.get("execution_profile", "scientific_wasm"),
                    candidate_artifact=candidate,
                )
            summary = _hidden_execution_summary(execution, evaluator=evaluator, required_estimator_id=required_id)
            summary.update({key: execution[key] for key in
                            ("execution_profile", "backend", "request_path", "request_hash") if key in execution})
            row["execution"] = summary
            passed = summary["passed"]
        if dimension == "theory":
            if authority:
                row["assessment_authority"] = "external_adjudication_record"
                if review is None:
                    row["status"] = "pending_adjudication" if passed else "failed"
                    continue
                row["external_review_hash"] = stable_hash(review)
                row["external_review_verdict"] = review["verdict"]
                review_dir = out_dir / "theory"
                review_dir.mkdir(exist_ok=True)
                (review_dir / "external_review.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
                (review_dir / "assessment_protocol.txt").write_bytes(protocol.encode("utf-8"))
                (review_dir / "assessment_report.txt").write_bytes(report.encode("utf-8"))
                row["status"] = ({"accepted": "passed", "rejected": "failed", "unresolved": "unresolved"}[review["verdict"]]
                                 if passed else "failed")
                continue
            # A structural artifact check alone cannot accept a mathematical argument.
            if not semantic:
                row["status"] = "unconfigured"
                continue
            row["assessment_authority"] = "local_model_review"
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
              "submitted_material_hash": material_hash, "dimension_status": dimensions,
              "task_passed": bool(required) and all(row["status"] == "passed" for row in required),
              "internal_acceptance_required": False, "runtime_feedback_generated": False,
              "evaluation_role": "external_publication_outcome_not_product_acceptance_or_proof"}
    (out_dir / "outcome.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
