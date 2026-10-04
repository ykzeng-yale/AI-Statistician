"""Native final-file snapshots, not model inference or statistical efficacy."""

import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from ai_statistician.fingerprint import stable_hash
from ai_statistician.research_control import collect_native_research_submission, load_native_research_submission
from ai_statistician.research_gold_evaluation import _hidden_execution_summary, _run_hidden_scientific_harness
from ai_statistician.research_schema import OpenResearchQuestion, research_question_payload
from ai_statistician.scientific_project import scientific_project_hash
from ai_statistician.scientific_sandbox import ScientificEstimatorBinding, discover_scientific_sandbox_runtime
from benchmarks.publication.evaluate_final_artifacts import native_final_artifact_paths


def native_fixture(tmp_path, *, language="python", offset=0, returncode=0):
    root = tmp_path / "author"
    root.mkdir()
    helper = "helper.py" if language == "python" else "helper.R"
    main = "main.py" if language == "python" else "main.R"
    code = ("from helper import echo_value\n"
            "def run_estimator(request):\n    return {'echo': echo_value(request['value'])}\n"
            if language == "python" else
            "source('helper.R')\nrun_estimator <- function(request) list(echo=echo_value(request$value))\n")
    support = (f"def echo_value(value):\n    return value + {offset}\n" if language == "python" else
               f"echo_value <- function(value) value + {offset}\n")
    files = {"report.md": b"# Unresolved opaque record\n", "theory/claim.tex": b"Unresolved, not a theorem.\n",
             "code/" + main: code.encode(), "code/" + helper: support.encode(),
             "experiments/raw.bin": b"\x00\xff\x01", "drafts/earlier.csv": b"opaque,value\na,1\n"}
    # A real local process writes scripted fixtures; it is not a native coding host/model draw.
    script = ("from pathlib import Path\n"
              f"files = {files!r}\n"
              "for name, raw in files.items():\n"
              "    path = Path(name)\n    path.parent.mkdir(parents=True, exist_ok=True)\n    path.write_bytes(raw)\n"
              "print('opaque process observation')\n"
              f"raise SystemExit({returncode})\n")
    process = subprocess.run([sys.executable, "-c", script], cwd=root, capture_output=True, timeout=10)
    question = OpenResearchQuestion("opaque", "Opaque final files", "No statistical result is established.",
                                    task_intent={"theory": "required", "scientific_code": "required", "formal": "optional"})
    paths = {"report": ["report.md"], "theory": ["theory/claim.tex"], "scientific_code": ["code/" + main, "code/" + helper],
             "empirical": ["experiments/raw.bin", "experiments/final.csv"], "formal": ["formal/Target.lean"]}
    store = tmp_path / "evaluator-snapshot"
    return root, store, question, paths, process, files


@pytest.mark.parametrize("returncode", [0, 19])
def test_snapshot_keeps_exact_final_bytes_and_missing_outputs_after_process_termination(tmp_path, returncode):
    root, store, question, paths, process, files = native_fixture(tmp_path, returncode=returncode)
    ref = collect_native_research_submission(question=question, workspace_root=root, artifact_paths=paths,
                                             host_result=process, snapshot_dir=store)
    (root / "report.md").write_text("later source change", encoding="utf-8")
    (root / "code/main.py").unlink()
    result = load_native_research_submission(ref, question=question, artifact_paths=paths, snapshot_dir=store)
    assert result["artifact_bytes"]["report"]["report.md"] == files["report.md"]
    assert result["artifact_bytes"]["scientific_code"]["code/main.py"] == files["code/main.py"]
    assert result["artifact_bytes"]["empirical"] == {"experiments/raw.bin": b"\x00\xff\x01"}
    assert result["missing_artifacts"]["empirical"] == ["experiments/final.csv"]
    assert result["missing_artifacts"]["formal"] == ["formal/Target.lean"]
    assert result["host_process"]["returncode"] == returncode
    assert result["host_process"]["stdout_sha256"] == hashlib.sha256(process.stdout).hexdigest()
    assert result["evidence_role"] == "submission_not_scientific_acceptance"
    assert "task_passed" not in result and "independent_role_review" not in result
    assert "drafts/earlier.csv" not in str(result)  # No latest/best/intermediate salvage.
    with pytest.raises(FileExistsError):
        collect_native_research_submission(question=question, workspace_root=root, artifact_paths=paths,
                                           host_result=process, snapshot_dir=store)


@pytest.mark.parametrize("change", ["record", "blob", "question", "paths", "record_link", "blob_link"])
def test_changed_native_snapshot_identities_are_rejected(tmp_path, change):
    root, store, question, paths, process, _ = native_fixture(tmp_path)
    ref = collect_native_research_submission(question=question, workspace_root=root, artifact_paths=paths,
                                             host_result=process, snapshot_dir=store)
    record = store / "submission.json"
    blob = Path(json.loads(record.read_text())["artifact_refs"]["report"]["report.md"]["path"])
    if change == "record":
        record.write_text("{}")
    elif change == "blob":
        blob.write_bytes(b"different")
    elif change == "question":
        question = replace(question, task_intent={"theory": "optional"})
    elif change == "paths":
        paths = {**paths, "report": ["other.md"]}
    else:
        target = record if change == "record_link" else blob
        escaped = tmp_path / "outside"
        escaped.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(escaped)
    with pytest.raises(ValueError):
        load_native_research_submission(ref, question=question, artifact_paths=paths, snapshot_dir=store)


def test_uncaptured_native_streams_remain_unknown_not_empty_verified_output(tmp_path):
    root, store, question, paths, process, _ = native_fixture(tmp_path)
    receipt = subprocess.CompletedProcess(args=process.args, returncode=process.returncode)
    ref = collect_native_research_submission(question=question, workspace_root=root, artifact_paths=paths,
                                             host_result=receipt, snapshot_dir=store)
    result = load_native_research_submission(ref, question=question, artifact_paths=paths, snapshot_dir=store)
    assert result["host_process"]["stdout_sha256"] is None
    assert result["host_process"]["stderr_sha256"] is None


def test_frozen_final_roots_collect_arbitrary_filenames_and_binary_files_without_draft_selection(tmp_path):
    root, store, question, _, process, _ = native_fixture(tmp_path)
    files = {"final/theory/claims/note.tex": b"Unresolved opaque claim.\r\n",
        "final/code/entry.py": b"# Opaque unexecuted source.\n",
        "final/code/helpers/nested.py": b"# Opaque support.\n",
        "final/empirical/results.bin": b"\xff\x00\x01"}
    for name, raw in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    roots = {"theory": "final/theory", "scientific_code": "final/code", "empirical": "final/empirical",
             "report": "final/report", "formal": "final/formal"}
    paths = native_final_artifact_paths(workspace_root=root, artifact_roots=roots)
    assert paths["scientific_code"] == ["final/code/entry.py", "final/code/helpers/nested.py"]
    assert paths["report"] == paths["formal"] == []
    assert not any("earlier" in name for names in paths.values() for name in names)
    ref = collect_native_research_submission(question=question, workspace_root=root, artifact_paths=paths,
        host_result=process, snapshot_dir=store)
    for name in files:
        (root / name).unlink()
    result = load_native_research_submission(ref, question=question, artifact_paths=paths, snapshot_dir=store)
    assert {name: raw for scope in result["artifact_bytes"].values() for name, raw in scope.items()} == files
    assert result["artifact_bytes"]["report"] == {}  # No report is invented from a draft outside the final tree.


@pytest.mark.parametrize("bad", ["empty", "dot", "parent", "absolute", "noncanonical", "overlap", "duplicate",
                                 "root_symlink", "file_symlink", "not_directory"])
def test_native_final_roots_reject_ambiguous_or_escaping_trees(tmp_path, bad):
    root = tmp_path / "workspace"
    root.mkdir()
    roots = {"theory": "final/theory", "source": "final/code"}
    if bad == "empty":
        roots = {}
    elif bad in {"dot", "parent", "absolute", "noncanonical"}:
        roots["theory"] = {"dot": ".", "parent": "../other", "absolute": "/other", "noncanonical": "final//theory"}[bad]
    elif bad == "overlap":
        roots["source"] = "final/theory/code"
    elif bad == "duplicate":
        roots["source"] = roots["theory"]
    else:
        (root / "final").mkdir()
        if bad == "not_directory":
            (root / "final/theory").write_text("not a directory")
        elif bad == "root_symlink":
            outside = tmp_path / "other"
            outside.mkdir()
            (root / "final/theory").symlink_to(outside, target_is_directory=True)
        else:
            (root / "final/theory").mkdir()
            outside = tmp_path / "other.tex"
            outside.write_text("not selected research")
            (root / "final/theory/link.tex").symlink_to(outside)
    with pytest.raises(ValueError):
        native_final_artifact_paths(workspace_root=root, artifact_roots=roots)
    assert not (root / "submission.json").exists()


@pytest.mark.parametrize("bad", ["../outside", "/absolute", "a/../b", "./report.md", "a\\b", "duplicate", "string", "symlink", "in_workspace", "running"])
def test_collection_rejects_invalid_paths_stores_and_nonterminal_receipts(tmp_path, bad):
    root, store, question, paths, process, _ = native_fixture(tmp_path)
    if bad == "duplicate":
        paths = {"report": ["report.md", "report.md"]}
    elif bad == "string":
        paths = {"report": "report.md"}
    elif bad == "symlink":
        target = tmp_path / "outside"
        target.write_bytes(b"not author content")
        (root / "escape.md").symlink_to(target)
        paths = {"report": ["escape.md"]}
    elif bad == "in_workspace":
        store = root / "snapshot"
    elif bad == "running":
        process = subprocess.CompletedProcess(args=["opaque"], returncode=None)
    else:
        paths = {"report": [bad]}
    with pytest.raises(ValueError):
        collect_native_research_submission(question=question, workspace_root=root, artifact_paths=paths,
                                           host_result=process, snapshot_dir=store)
    assert not (store / "submission.json").exists()


@pytest.mark.parametrize("language", ["python", "r"])
@pytest.mark.parametrize("offset", [0, 1])
def test_hidden_executor_consumes_the_frozen_native_multifile_source_not_later_workspace(tmp_path, language, offset, monkeypatch):
    monkeypatch.delenv("AI_STATISTICIAN_NATIVE_PROJECT_CONFIG", raising=False)
    runtime = discover_scientific_sandbox_runtime()
    if not (runtime.python_available if language == "python" else runtime.r_available):
        pytest.skip("scientific runtime is not prepared")
    root, store, question, paths, process, _ = native_fixture(tmp_path, language=language, offset=offset, returncode=19 if offset == 0 else 0)
    ref = collect_native_research_submission(question=question, workspace_root=root, artifact_paths=paths,
                                             host_result=process, snapshot_dir=store)
    before = (store / "submission.json").read_bytes()
    for relative in paths["scientific_code"]:
        (root / relative).write_text("later invalid source", encoding="utf-8")
    result = load_native_research_submission(ref, question=question, artifact_paths=paths, snapshot_dir=store)
    source = result["artifact_bytes"]["scientific_code"]
    main, helper = paths["scientific_code"]
    code = source[main].decode("utf-8")
    support = [{"path": helper.removeprefix("code/"), "content": source[helper].decode("utf-8")}]
    binding = ScientificEstimatorBinding(artifact_id="opaque", language=language, code=code, code_hash=stable_hash(code),
                                        dependencies=(), project_files=tuple(support),
                                        project_hash=scientific_project_hash(language=language, code=code, project_files=support))
    held = ("def run_sandbox(seed, replicates, estimators):\n"
            "    return estimators['opaque']({'value': seed + replicates})\n" if language == "python" else
            "run_sandbox <- function(seed, replicates, estimators) estimators[['opaque']](list(value=seed+replicates))\n")
    raw = _run_hidden_scientific_harness(sandbox_dir=tmp_path / "evaluator-only", artifact_id="native-final-source",
                                        harness_language=language, harness_code=held, harness_dependencies=(),
                                        estimator_binding=binding, seed=99173, replicates=5, timeout_s=30)
    summary = _hidden_execution_summary(raw, evaluator={"acceptance_checks": [{"check_id": "opaque-held-value",
        "path": ["echo"], "operator": "eq", "expected": 99178}]}, required_estimator_id="opaque")
    assert summary["execution_passed"] and summary["estimator_invocation_count"] == 1
    assert summary["passed"] is (offset == 0)
    assert raw["estimator_project_hashes"] == {"opaque": binding.project_hash}
    assert raw["metrics"] == {"echo": 99178 + offset}
    assert (store / "submission.json").read_bytes() == before
    assert "99173" not in process.args[-1] and "99178" not in process.args[-1]

    # Prospective external outcomes consume this final snapshot, not the host's exit verdict.
    # Semantic failure is scripted; no mathematical authority or live model is claimed.
    from benchmarks.publication import evaluate_final_artifacts as outcomes
    from ai_statistician.research_gold_evaluation import _visible_question_hash_payload
    authority = tmp_path / "private-harness"
    authority.write_text(held)
    public = research_question_payload(question, include_task_intent=True)
    task = {"task_id": question.id, "task_intent": question.task_intent,
            "visible_question_hash": stable_hash(_visible_question_hash_payload(public)),
            "hidden_algorithm_evaluator": {"language": language, "harness_path": str(authority),
                "harness_sha256": hashlib.sha256(held.encode()).hexdigest(), "required_estimator_id": "opaque",
                "seed": 99173, "replicates": 5, "timeout_seconds": 30,
                "acceptance_checks": [{"path": ["echo"], "operator": "eq", "expected": 99178}]},
            "hidden_theory_semantic_evaluator": {"provider": "local"}}
    theory = [{"path": relative, "content": raw.decode(), "sha256": hashlib.sha256(raw).hexdigest()}
              for relative, raw in result["artifact_bytes"]["theory"].items()]
    reviews = []
    def review(**kwargs):
        reviews.append(kwargs["candidate_documents"])
        judgment = {"passed": False, "mechanism_fixture_not_scientific_authority": True}
        return {**judgment, "judgment_hash": stable_hash(judgment)}, ""
    monkeypatch.setattr(outcomes, "_run_hidden_document_semantic_evaluation", review)
    outcome = outcomes.evaluate_final_research_artifacts(
        question=question, task=task, submission_identity=result, project_root=tmp_path, out_dir=tmp_path / "common-outcome",
        theory_documents=theory, estimator_bindings=(binding,),
    )
    assert outcome["dimension_status"]["scientific_code"]["status"] == ("passed" if offset == 0 else "failed")
    assert outcome["dimension_status"]["theory"]["status"] == "failed" and outcome["task_passed"] is False
    assert reviews == [theory] and (store / "submission.json").read_bytes() == before
