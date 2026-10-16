"""Apply the scoped patch to exact Sakana sources, then exercise their real modules.

Authors, ideation and scientific reviewers are deterministic fixtures. Native
harness evaluation runs a small local Python evaluator; these are mechanism
tests, not research E2E evidence.
Sakana AI retains upstream Apache-2.0 attribution. No models or remote jobs run.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party/ai-scientist-v3"
PYTHON = UPSTREAM / ".venv/bin/python"
PATCH = ROOT / "integrations/agentic-scientist/native_campaign_semantics.patch"
PIN = "2b8aa39285c35aaca3b0e06dd121061ef8a2d854"
OWNED_MODULES = {
    "src/investigation/main_entry.py", "src/investigation/harness_incumbent.py",
    "src/investigation/idea_generation.py", "src/investigation/campaign_loop.py",
    "src/investigation/harness_eval.py",
    "src/agents/skills/create-idea/SKILL.md", "src/prompts/idea.md", "src/scripts/idea.sh",
}
REQUIREMENTS = [
    {"id": "target", "description": "Meet the operator target", "type": "metric",
     "metric": "combined_score", "operator": ">=", "threshold": 2},
    {"id": "implementation", "description": "Executable solve implementation",
     "type": "implementation", "verification": {"type": "source_contains", "patterns": ["solve"]}},
]
SPEC = '''schema_version = 1
code_root = "src"
[entrypoint]
path = "program.py"
language = "python"
type = "script"
[copy]
exclude = []
include = []
[integration]
kind = "generic"
notes = ""
'''
EVALUATOR = '''import argparse, json, runpy
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--program_path")
p.add_argument("--results_dir")
a = p.parse_args()
counter = Path("evaluation_count")
counter.write_text(str(int(counter.read_text()) + 1) if counter.exists() else "1")
candidate = runpy.run_path(a.program_path)
value = candidate["solve"]()
out = Path(a.results_dir)
(out / "metrics.json").write_text(json.dumps({"combined_score": value}))
(out / "correct.json").write_text(json.dumps({"correct": candidate["VALID"]}))
print("fixture evaluator completed")
'''
REVIEW_RUBRICS = [
    {"id": "theory", "description": "Review the scientific argument", "type": "review",
     "verification": {"type": "source_contains", "patterns": ["solve"]}},
    {"id": "method", "description": "Review the method", "type": "review",
     "metric": "combined_score", "operator": ">=", "threshold": 0},
]
REVIEWER = r'''import argparse, hashlib, json, os, signal, sys, time
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--stage", choices=["review"], required=True)
p.add_argument("--program-dir", type=Path, required=True)
p.add_argument("--task-dir", type=Path, required=True)
p.add_argument("--rubrics-file", type=Path, required=True)
p.add_argument("--model", required=True)
a = p.parse_args()
program = a.program_dir
read = lambda path: json.loads(path.read_text())
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
json_digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()
manifest = read(program / "evaluation_manifest.json")
assert manifest["exit_code"] == 0 and not manifest.get("completed")
assert not (program / "rubric_status.json").exists()
assert not (a.task_dir / "rubric_status.json").exists()
assert sys.stdin.read() == ""
record_path = Path(os.environ["FIXTURE_REVIEW_RECORD"])
records = read(record_path) if record_path.exists() else []
records.append({"argv": sys.argv[1:], "cwd": str(Path.cwd())})
record_path.write_text(json.dumps(records))
print("raw reviewer stdout", flush=True)
print("raw reviewer stderr", file=sys.stderr, flush=True)
mode = os.environ["FIXTURE_REVIEW_MODE"]
rubrics = read(a.rubrics_file)
review_ids = [item["id"] for item in rubrics if item["type"] == "review"]
status = mode if mode in ("PASS", "FAIL", "UNCERTAIN") else "PASS"
if mode == "campaign_fail_then_pass" and len(records) == 1:
    status = "FAIL"
report = program / "scientific_review.md"
report.write_text("# Deterministic reviewer report\nFixture finding: " + status + "\n")
session = program / ".scientific-review/session/result.json"
session.parent.mkdir(parents=True)
session.write_text(json.dumps({"status": "completed", "fixture": True}))
summary = {
    "schema_version": 1, "kind": "ai_scientific_review", "model": a.model,
    "task_sha256": digest(a.task_dir / "task.md"), "rubrics_sha256": json_digest(rubrics),
    "source_records": manifest["source_records"],
    "verdicts": [{"id": key, "status": status if key == review_ids[0] else "PASS"}
                 for key in reversed(review_ids)],
    "report": {"path": "scientific_review.md", "sha256": digest(report)},
    "session": {"path": ".scientific-review/session/result.json", "sha256": digest(session)},
    "scope": "AI source review, not proof or independent empirical confirmation.",
}
if mode.startswith("stale_") and mode[6:] in ("task", "rubrics", "model", "source"):
    field = {"task": "task_sha256", "rubrics": "rubrics_sha256",
             "model": "model", "source": "source_records"}[mode[6:]]
    summary[field] = {} if field == "source_records" else "stale"
elif mode == "rubrics_subset":
    summary["rubrics_sha256"] = json_digest([r for r in rubrics if r["type"] == "review"])
elif mode == "missing_input":
    summary["source_records"].pop("input.bin")
elif mode in ("stale_report", "stale_session"):
    path = report if mode == "stale_report" else session
    path.write_text(path.read_text() + "\n")
elif mode in ("missing_report", "missing_session"):
    (report if mode == "missing_report" else session).unlink()
elif mode in ("report_path", "session_path"):
    summary[mode.split("_")[0]]["path"] = "../wrong-file"
elif mode == "live_task_changed":
    (a.task_dir / "task.md").write_text("Changed staged task")
elif mode == "live_source_changed":
    path = program / "src/program.py"
    path.write_text(path.read_text() + "\n")
elif mode == "live_rubrics_changed":
    a.rubrics_file.write_text(json.dumps(rubrics[:-1]))
elif mode in ("wrong_schema", "wrong_kind", "empty_scope"):
    field, value = {"wrong_schema": ("schema_version", True),
                    "wrong_kind": ("kind", "author_report"), "empty_scope": ("scope", " ")}[mode]
    summary[field] = value
elif mode == "missing_verdict":
    summary["verdicts"].pop()
elif mode == "extra_verdict":
    summary["verdicts"].append({"id": "target", "status": "PASS"})
elif mode == "duplicate_verdict":
    summary["verdicts"][1] = summary["verdicts"][0]
elif mode == "wrong_verdict_id":
    summary["verdicts"][0]["id"] = "target"
elif mode == "bad_status":
    summary["verdicts"][0]["status"] = "passed"
elif mode == "malformed_verdict":
    summary["verdicts"][0] = {"id": [], "status": ["PASS"]}
elif mode == "extra_verdict_field":
    summary["verdicts"][0]["explanation"] = "Not in the verdict contract"
payload = json.dumps(summary)
if mode == "malformed":
    payload = "{"
elif mode == "not_object":
    payload = "[]"
elif mode == "invalid_utf8":
    payload = None
if mode != "missing":
    (program / "scientific_review.json").write_bytes(payload.encode() if payload is not None else b"\xff")
if mode == "exit_failure":
    sys.exit(23)
if mode == "interrupted":
    os.kill(os.getpid(), signal.SIGTERM)
if mode == "timeout":
    time.sleep(60)
'''


@pytest.fixture(scope="module")
def patched_upstream(tmp_path_factory):
    if not PYTHON.exists():
        pytest.skip("Install the pinned upstream environment for native mechanism tests")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=UPSTREAM, text=True).strip() == PIN
    archive = subprocess.check_output(["git", "archive", PIN], cwd=UPSTREAM)
    destination = tmp_path_factory.mktemp("native-campaign-pinned")
    with tarfile.open(fileobj=io.BytesIO(archive)) as sources:
        sources.extractall(destination, filter="data")
    before = {str(p.relative_to(destination)): p.read_bytes() for p in destination.rglob("*") if p.is_file()}
    for flags in (["--check"], []):
        result = subprocess.run(["git", "apply", *flags, str(PATCH)], cwd=destination, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
    changed = {name for name, content in before.items() if (destination / name).read_bytes() != content}
    assert changed == OWNED_MODULES
    assert (destination / "LICENSE").read_bytes() == before["LICENSE"]
    assert PIN in PATCH.read_text() and "Sakana" in PATCH.read_text()
    return destination


def test_idea_prompt_and_skill_share_the_actual_task_contract(patched_upstream, tmp_path):
    code = r'''
import json, sys
from pathlib import Path
from src.investigation.idea_generation import idea_artifact_contract
task = Path(sys.argv[1])
for fixed in (False, True):
    if fixed:
        (task / "target_rubrics.json").write_text(json.dumps([
            {"id": "opaque", "description": "Opaque host criterion", "type": "metric",
             "metric": "combined_score", "operator": ">=", "threshold": 3}]))
    for harness in (False, True):
        contract = idea_artifact_contract(task, harness_evaluated_attempt=harness)
        for name in ("src/prompts/idea.md", "src/agents/skills/create-idea/SKILL.md"):
            rendered = Path(name).read_text()
            for key, value in contract.items():
                rendered = rendered.replace("{{" + key + "}}", value)
            assert "{{IDEA_ARTIFACT_REQUIREMENTS}}" not in rendered
            assert "{{HARNESS_RUBRIC_REQUIREMENTS}}" not in rendered
            if fixed:
                assert "Write only ./idea_bundle.json" in rendered
                assert "source_contains" not in rendered
                assert "at least one metric" not in rendered
            else:
                assert "identical rubric array" in rendered
                assert ("source_contains" in rendered) == harness
'''
    run = subprocess.run([str(PYTHON), "-c", code, str(tmp_path)], cwd=patched_upstream,
                         capture_output=True, text=True, timeout=20)
    assert run.returncode == 0, run.stdout + run.stderr


SCENARIOS = [
    "cold_start", "optimization", "frozen_rubrics", "fail_then_pass", "partial_then_pass",
    "false_correctness", "unsupported_review", "exhaustion_resume", "completed_resume",
    "changed_task", "changed_seed", "changed_evaluator", "changed_criteria", "removed_criteria",
    "wrong_task", "corrupt_state", "corrupt_best", "reset_existing", "stale_candidate",
    "stale_metrics", "stale_correctness", "stale_status", "stale_log", "stale_manifest",
    "arbitrary_json", "copied_receipt", "orphan_evidence", "wrong_cycle", "missing_history",
    "preexisting_seed_evidence", "malformed_requirements", "native_failure", "no_rescore",
    "evidence_tamper_before_promotion", "source_tamper_before_promotion",
    "result_artifacts", "result_artifacts_optimization", "stale_result_artifact", "stale_input",
]
REVIEW_SCENARIOS = [
    "PASS", "FAIL", "UNCERTAIN", "missing", "malformed", "not_object", "invalid_utf8",
    "stale_source", "stale_report", "stale_session", "stale_task", "stale_rubrics", "stale_model",
    "rubrics_subset", "missing_input", "missing_report", "missing_session", "report_path", "session_path",
    "live_task_changed", "live_source_changed", "live_rubrics_changed",
    "wrong_schema", "wrong_kind", "empty_scope", "missing_verdict", "extra_verdict",
    "duplicate_verdict", "wrong_verdict_id", "bad_status", "malformed_verdict", "extra_verdict_field",
    "exit_failure", "interrupted", "timeout", "launch_failure", "preexisting",
    "no_python", "no_entrypoint", "no_model", "unconfigured", "no_review", "sealed",
    "incorrect", "truthy_correct", "evaluation_failed", "nonzero_correct",
    "tamper_summary", "tamper_report", "tamper_session", "tamper_stdout", "tamper_stderr",
    "campaign_pass", "campaign_fail_then_pass",
]


@pytest.mark.parametrize("scenario", SCENARIOS + ["review_" + name for name in REVIEW_SCENARIOS])
def test_native_campaign_scenario(patched_upstream, tmp_path, scenario):
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path), "PYTHONDONTWRITEBYTECODE": "1",
    }
    result = subprocess.run(
        [str(PYTHON), str(Path(__file__).resolve()), scenario, str(patched_upstream), str(tmp_path)],
        cwd=patched_upstream, env=environment, capture_output=True, text=True, timeout=40,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def _read(path):
    return json.loads(path.read_text())


def _snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def _task(root, requirements=REQUIREMENTS):
    task = root / "task"
    (task / "program_0/src").mkdir(parents=True)
    (task / "program_0/program_spec.toml").write_text(SPEC)
    (task / "program_0/src/program.py").write_text("VALID = False\ndef solve():\n    return 0\n")
    (task / "program_0/input.bin").write_bytes(b"opaque pre-evaluation input")
    (task / "task.md").write_text("# Opaque deterministic fixture\nReconstruct the fixed target.\n")
    (task / "capture.py").write_text("")
    (task / "evaluate.py").write_text(EVALUATOR)
    if requirements is not None:
        _write_json(task / "target_rubrics.json", requirements)
    return task


def _campaign(task, results, candidates=(), *, cycles=1, resume=False, no_idea=False, tamper=None):
    from src.investigation.config import InvestigationConfig
    from src.investigation.main_entry import run_main_flow
    from src.investigation.models import IdeaGenerationResult, RunAttemptResult
    from src.investigation.harness_eval import run_harness_evaluation
    from src.investigation.program_clone import clone_program_dir
    from src.orchestrator import state

    cfg = InvestigationConfig()
    cfg.agent.name = "codex"
    cfg.agent.model = "inert-fixture-no-model"
    cfg.paths.task_dir = str(task)
    cfg.paths.results_dir = str(results)
    cfg.execution.harness_evaluated_attempts = True
    cfg.execution.draft_task_if_missing = False
    cfg.execution.resume = resume
    cfg.execution.max_idea_cycles = cycles
    cfg.execution.max_idea_generation_attempts = 1
    cfg.execution.prune_every_n_cycles = 0
    cfg.execution.workers = 1
    cfg.paper.enabled = False
    cfg.versioning.enabled = False
    events, attempts, ideas = [], [], []
    remaining = iter(candidates)

    def deny(*args, **kwargs):
        raise AssertionError("unexpected external action")

    def idea(**kwargs):
        ideas.append(kwargs)
        workspace = kwargs["output_dir"]
        workspace.mkdir(parents=True)
        if no_idea:
            return IdeaGenerationResult(output="inert idea failure", exit_code=1, idea_dir=workspace)
        weakened = [{"id": "weak", "description": "combined_score >= -999", "type": "metric"}]
        _write_json(workspace / "idea_bundle.json", {
            "idea_id": f"idea_{kwargs['cycle_index']:04d}", "title": "Fixture revision",
            "hypothesis": "Check the next source revision", "implementation_plan": ["Revise source"],
            "target_rubrics": weakened,
        })
        _write_json(workspace / "target_rubrics.json", weakened)
        return IdeaGenerationResult(output="inert idea", exit_code=0, idea_dir=workspace)

    def attempt(**kwargs):
        score, valid = next(remaining)
        experiment = state.idea_dir(results, kwargs["idea_dir_name"]) / "01_attempt"
        experiment.mkdir()
        clone_program_dir(src_dir=kwargs["seed_program_dir"], dst_dir=experiment / "program_0")
        clone_program_dir(src_dir=experiment / "program_0", dst_dir=experiment / "program_1")
        source = experiment / "program_1/src/program.py"
        source.write_text(f"VALID = {valid!r}\ndef solve():\n    return {score!r}\n")
        if score == "crash":
            source.write_text("def solve():\n    raise RuntimeError('preserved fixture failure')\n")
        shutil.copy2(task / "evaluate.py", experiment / "evaluate.py")
        shutil.copy2(task / "task.md", experiment / "task.md")
        assert _read(kwargs["rubrics_file"]) == _read(task / "target_rubrics.json")
        arguments = dict(
            experiment_dir=experiment, attempt_id=kwargs["attempt_id"],
            idea_id=_read(kwargs["idea_file"])["idea_id"], rubrics_path=kwargs["rubrics_file"],
            python_bin=sys.executable, global_memory_md=results / "global_memory.md",
            global_memory_jsonl=results / "global_memory.jsonl", timeout_seconds=5,
        )
        exit_code = run_harness_evaluation(**arguments)
        attempts.append((experiment, arguments, _snapshot(experiment / "program_1")))
        if tamper is not None:
            tamper(experiment)
        return RunAttemptResult(output="inert author; real evaluator", exit_code=exit_code, experiment_dir=experiment)

    instruction = Path("src/prompts/general.md").resolve()
    code = run_main_flow(
        cfg=cfg, main_started_at=time.monotonic(), set_active_container_session_fn=deny,
        build_container_session_name_fn=deny, stop_container_session_fn=deny,
        probe_docker_available_fn=deny, docker_image_exists_fn=deny, docker_binary_lookup_fn=deny,
        default_results_path_fn=deny, default_instruction_path_fn=lambda *_: instruction,
        default_idea_instruction_path_fn=lambda: instruction,
        default_draft_instruction_path_fn=lambda: instruction,
        default_paper_instruction_path_fn=lambda: instruction,
        normalize_agent_results_dir_fn=deny,
        log_event_fn=lambda event, **kw: events.append((event, kw)),
        log_step_start_fn=lambda *a, **k: time.monotonic(), log_step_end_fn=lambda *a, **k: None,
        run_task_drafting_fn=deny, run_parallel_campaign_fn=deny, run_idea_generation_fn=idea,
        run_single_attempt_fn=attempt, run_paper_generation_fn=deny,
        run_task_setup_fn=lambda *a: True, prepare_task_runtime_fn=deny,
        reconcile_legacy_idea_local_memory_fn=lambda **k: None, format_elapsed_fn=str,
    )
    return code, events, attempts, ideas


def _run_scenario(name, root):
    from src.investigation.harness_eval import run_harness_evaluation
    from src.investigation.idea_generation import load_fixed_target_rubrics, load_idea_artifacts
    from src.investigation.harness_incumbent import read_native_evaluation

    if name.startswith("review_"):
        return _run_review_scenario(name.removeprefix("review_"), root)
    task = _task(root)
    results = root / "results"
    if name in {"result_artifacts", "result_artifacts_optimization", "stale_result_artifact"}:
        with (task / "evaluate.py").open("a") as output:
            output.write("(out / 'study').mkdir()\n(out / 'study/result.csv').write_text('a,b\\n1,2\\n')\n")
            output.write("(out / 'plot.bin').write_bytes(bytes(range(32)))\n")
    if name == "cold_start":
        code, events, attempts, ideas = _campaign(task, results, no_idea=True)
        assert code == 2 and len(ideas) == 1 and not attempts
        best = _read(results / "best_program_manifest.json")
        assert best["combined_score"] is None and best["correct"] is None
        assert best["source_attempt_id"] == "bootstrap"
        assert not (Path(best["program_dir"]) / "metrics.json").exists()
        assert not any(e[1].get("reason") == "missing_validated_harness_incumbent" for e in events)
        return
    if name == "optimization":
        (task / "target_rubrics.json").unlink()
        code, events, attempts, ideas = _campaign(task, results)
        assert code == 2 and not ideas and not attempts
        assert any(e[1].get("reason") == "missing_validated_harness_incumbent" for e in events)
        workspace = root / "idea"
        _write_json(workspace / "idea_bundle.json", {
            "title": "Optimize", "hypothesis": "Improve", "implementation_plan": ["Edit"],
            "target_rubrics": REQUIREMENTS,
        })
        _write_json(workspace / "target_rubrics.json", REQUIREMENTS)
        artifacts = load_idea_artifacts(workspace, 1, _read, require_harness_verification=True, harness_incumbent_score=5)
        assert artifacts.target_rubrics[0]["id"] == "incumbent_score_improvement"
        assert artifacts.target_rubrics[0]["threshold"] == 5
        assert load_fixed_target_rubrics(task) is None
        return
    if name == "frozen_rubrics":
        frozen = load_fixed_target_rubrics(task)
        assert frozen == REQUIREMENTS and frozen[0]["threshold"] == 2
        workspace = root / "idea"
        _write_json(workspace / "idea_bundle.json", {
            "title": "Fixed", "hypothesis": "Revise", "implementation_plan": ["Edit"],
            "target_rubrics": [],
        })
        for score in (None, -10, 99):
            artifacts = load_idea_artifacts(workspace, 1, _read, require_harness_verification=True,
                                           harness_incumbent_score=score, fixed_target_rubrics=frozen)
            assert artifacts.target_rubrics == REQUIREMENTS
            artifacts.target_rubrics[0]["threshold"] = -999
            assert frozen == REQUIREMENTS
        return
    if name == "preexisting_seed_evidence":
        _write_json(task / "program_0/metrics.json", {"combined_score": 99})
        code, _, attempts, ideas = _campaign(task, results)
        assert code == 2 and not ideas and not attempts and not results.exists()
        return
    if name == "malformed_requirements":
        for invalid in ([], {}, [REQUIREMENTS[0], REQUIREMENTS[0]], [{**REQUIREMENTS[0], "threshold": "two"}]):
            _write_json(task / "target_rubrics.json", invalid)
            code, _, attempts, ideas = _campaign(task, results)
            assert code == 2 and not ideas and not attempts and not results.exists()
        return
    if name in {"fail_then_pass", "partial_then_pass", "native_failure"}:
        first = (0, False) if name == "fail_then_pass" else (1, True) if name == "partial_then_pass" else ("crash", False)
        code, events, attempts, ideas = _campaign(task, results, [first, (2, True)], cycles=4)
        assert code == 0 and len(attempts) == len(ideas) == 2
        assert _snapshot(attempts[0][0] / "program_1") == attempts[0][2]
        assert attempts[0][0] != attempts[1][0]
        assert all((a[0] / "evaluation_count").read_text() == "1" for a in attempts)
        history = [json.loads(line) for line in (results / "attempts_history.jsonl").read_text().splitlines()]
        assert [row["attempt_status"] for row in history] == ["fail", "pass"]
        assert [row["best_updated"] for row in history] == [False, True]
        assert _read(results / "outer_state.json")["task_complete"] is True
        assert any(event == "task_complete" for event, _ in events)
        return
    if name in {"false_correctness", "unsupported_review"}:
        if name == "unsupported_review":
            _write_json(task / "target_rubrics.json", REQUIREMENTS + [
                {"id": "review", "description": "Requires independent scientific assessment", "type": "review"},
            ])
        code, _, attempts, _ = _campaign(task, results, [(99, name == "unsupported_review")])
        assert code == 2 and len(attempts) == 1
        assert _read(results / "best_program_manifest.json")["combined_score"] is None
        assert _read(results / "outer_state.json")["task_complete"] is False
        return
    if name == "exhaustion_resume":
        code, _, attempts, _ = _campaign(task, results, [(1, True)])
        assert code == 2
        before = _snapshot(attempts[0][0])
        code, _, more, _ = _campaign(task, results, [(2, True)], cycles=3, resume=True)
        assert code == 0 and len(more) == 1 and _snapshot(attempts[0][0]) == before
        assert _read(results / "outer_state.json")["current_cycle"] == 2
        return
    if name == "result_artifacts_optimization":
        from src.investigation.program_clone import clone_program_dir
        rubrics_path = root / "optimization_rubrics.json"
        (task / "target_rubrics.json").rename(rubrics_path)
        experiment = root / "standalone"
        experiment.mkdir()
        clone_program_dir(src_dir=task / "program_0", dst_dir=experiment / "program_1")
        shutil.copy2(task / "evaluate.py", experiment / "evaluate.py")
        assert run_harness_evaluation(
            experiment_dir=experiment, attempt_id="optimization", idea_id="optimization",
            rubrics_path=rubrics_path, python_bin=sys.executable,
            global_memory_md=root / "memory.md", global_memory_jsonl=root / "memory.jsonl", timeout_seconds=5,
        ) == 0
        assert (experiment / "program_1/study/result.csv").exists()
        assert _read(experiment / "program_1/correct.json")["correct"] is False
        return
    if name in {"evidence_tamper_before_promotion", "source_tamper_before_promotion"}:
        def tamper(experiment):
            path = experiment / "program_1" / ("metrics.json" if name.startswith("evidence") else "src/program.py")
            path.write_text(path.read_text() + "\n")
        code, _, attempts, _ = _campaign(task, results, [(2, True)], tamper=tamper)
        assert code == 2 and _read(results / "best_program_manifest.json")["combined_score"] is None
        assert "native_evaluation_error" in _read_history(results)[0]
        return

    code, _, attempts, _ = _campaign(task, results, [(2, True)], cycles=3)
    assert code == 0 and len(attempts) == 1
    experiment, arguments, _ = attempts[0]
    program = experiment / "program_1"
    if name == "result_artifacts":
        receipt = _read(program / "evaluation_manifest.json")
        assert "study/result.csv" in receipt["evidence_records"]
        assert "plot.bin" in receipt["evidence_records"]
        assert "input.bin" in receipt["source_records"]
        assert "study/result.csv" not in receipt["source_records"]
        assert _campaign(task, results, resume=True, cycles=5)[0] == 0
        return
    if name == "completed_resume":
        before = _snapshot(experiment)
        code, _, more, ideas = _campaign(task, results, resume=True, cycles=5)
        assert code == 0 and not more and not ideas and _snapshot(experiment) == before
        return
    if name == "no_rescore":
        before = _snapshot(experiment)
        with pytest.raises(SystemExit, match="agent-created evaluator artifact"):
            run_harness_evaluation(**arguments)
        assert _snapshot(experiment) == before
        return
    if name == "copied_receipt":
        copied = root / "copied_attempt"
        shutil.copytree(experiment, copied)
        with pytest.raises(ValueError, match="stale native evaluation"):
            read_native_evaluation(copied / "program_1", REQUIREMENTS,
                                   attempt_id=arguments["attempt_id"], idea_id=arguments["idea_id"])
        return
    if name == "arbitrary_json":
        (program / "evaluation_manifest.json").unlink()
    elif name == "changed_task":
        (task / "task.md").write_text("Different task")
    elif name == "changed_seed":
        (task / "program_0/src/program.py").write_text("Different seed")
    elif name == "changed_evaluator":
        (task / "evaluate.py").write_text("Different evaluator")
    elif name == "changed_criteria":
        _write_json(task / "target_rubrics.json", [{**REQUIREMENTS[0], "threshold": 1}, REQUIREMENTS[1]])
    elif name == "removed_criteria":
        (task / "target_rubrics.json").unlink()
    elif name == "wrong_task":
        shutil.copytree(task, root / "other-task")
        task = root / "other-task"
    elif name in {"corrupt_state", "corrupt_best"}:
        (results / ("outer_state.json" if name == "corrupt_state" else "best_program_manifest.json")).write_text("{")
    elif name.startswith("stale_"):
        filename = {"candidate": "src/program.py", "metrics": "metrics.json", "correctness": "correct.json",
                    "status": "rubric_status.json", "log": "harness_evaluate_stdout.log",
                    "manifest": "evaluation_manifest.json", "result_artifact": "study/result.csv",
                    "input": "input.bin"}[name.removeprefix("stale_")]
        path = program / filename
        path.write_text(path.read_text() + "\n")
    elif name == "orphan_evidence":
        shutil.copytree(experiment, results / "ideas/unrecorded/01_attempt")
    elif name == "wrong_cycle":
        state = _read(results / "outer_state.json")
        _write_json(results / "outer_state.json", {**state, "current_cycle": 0})
    elif name == "missing_history":
        (results / "attempts_history.jsonl").unlink()
    elif name != "reset_existing":
        raise AssertionError(name)
    before = _snapshot(results)
    code, events, more, ideas = _campaign(task, results, resume=name != "reset_existing", cycles=4)
    assert code == 2 and not more and not ideas
    assert _snapshot(results) == before
    assert any(fields.get("reason") == "invalid_fixed_campaign" for _, fields in events)


def _read_history(results):
    return [json.loads(line) for line in (results / "attempts_history.jsonl").read_text().splitlines()]


def _run_review_scenario(name, root):
    from src.investigation import harness_eval
    from src.investigation.harness_incumbent import read_native_evaluation
    from src.investigation.program_clone import clone_program_dir

    requirements = REQUIREMENTS + REVIEW_RUBRICS if name != "no_review" else REQUIREMENTS
    if name.startswith("campaign_"):
        requirements = REQUIREMENTS + [
            {key: row[key] for key in ("id", "description", "type")} for row in REVIEW_RUBRICS
        ]
    task = _task(root, requirements)
    reviewer = root / "reviewer fixture ; literal.py"
    reviewer.write_text(REVIEWER)
    record_path = root / "reviewer-invocations.json"
    environment = dict(os.environ) | {
        "AI_STATISTICIAN_API_PYTHON": sys.executable,
        "AI_STATISTICIAN_API_ENTRYPOINT": str(reviewer),
        "AI_STATISTICIAN_API_MODEL": "fixture/model ; literal",
        "FIXTURE_REVIEW_MODE": name,
        "FIXTURE_REVIEW_RECORD": str(record_path),
    }
    if name.startswith("campaign_"):
        os.environ.update(environment)
        results = root / "results"
        count = 2 if name == "campaign_fail_then_pass" else 1
        code, events, attempts, _ = _campaign(task, results, [(2, True)] * count, cycles=3)
        assert code == 0 and len(attempts) == count, (code, events)
        assert len(_read(record_path)) == count
        assert [row["best_updated"] for row in _read_history(results)] == [False] * (count - 1) + [True]
        assert _read(results / "outer_state.json")["task_complete"] is True
        for experiment, _, snapshot in attempts:
            assert _snapshot(experiment / "program_1") == snapshot
            assert (experiment / "evaluation_count").read_text() == "1"
        before = {experiment: _snapshot(experiment) for experiment, _, _ in attempts}
        code, _, more, ideas = _campaign(task, results, resume=True, cycles=4)
        assert code == 0 and not more and not ideas
        assert all(_snapshot(experiment) == snapshot for experiment, snapshot in before.items())
        assert len(_read(record_path)) == count
        return

    experiment = root / "attempt with spaces"
    experiment.mkdir()
    program = experiment / "program_1"
    clone_program_dir(src_dir=task / "program_0", dst_dir=program)
    correct = False if name == "incorrect" else "yes" if name == "truthy_correct" else True
    (program / "src/program.py").write_text(f"VALID = {correct!r}\ndef solve():\n    return 2\n")
    shutil.copy2(task / "evaluate.py", experiment / "evaluate.py")
    shutil.copy2(task / "task.md", experiment / "task.md")
    if name == "evaluation_failed":
        (experiment / "evaluate.py").write_text("raise RuntimeError('fixture evaluator failed')\n")
    elif name == "nonzero_correct":
        with (experiment / "evaluate.py").open("a") as output:
            output.write("raise SystemExit(7)\n")
    if name in ("no_python", "no_entrypoint", "no_model"):
        environment.pop("AI_STATISTICIAN_API_" + name.removeprefix("no_").upper())
    elif name == "unconfigured":
        environment = {key: value for key, value in environment.items()
                       if not key.startswith("AI_STATISTICIAN_API_")}
    elif name == "launch_failure":
        environment["AI_STATISTICIAN_API_PYTHON"] = str(root / "missing-python")
    elif name == "preexisting":
        (program / "scientific_review.md").write_text("Keep this pre-existing report unchanged\n")

    sealed = None
    if name == "sealed":
        sealed = harness_eval.SealedHarnessConfig(task, "inert-no-container", None, environment)

        def inert_sealed_evaluation(**kwargs):
            _write_json(program / "metrics.json", {"combined_score": 2})
            _write_json(program / "correct.json", {"correct": True})
            harness_eval._write_sealed_evaluation_artifacts(
                program_dir=program, attempt_id=kwargs["attempt_id"], idea_id=kwargs["idea_id"],
                command=["inert-sealed-fixture"], returncode=0, diagnostic="sealed fixture",
            )
            return 0

        harness_eval._run_sealed_evaluation = inert_sealed_evaluation
    arguments = dict(
        experiment_dir=experiment, attempt_id="review_attempt", idea_id="review_idea",
        rubrics_path=task / "target_rubrics.json", python_bin=sys.executable,
        global_memory_md=root / "memory.md", global_memory_jsonl=root / "memory.jsonl",
        timeout_seconds=1 if name == "timeout" else 5, environment=environment, sealed_config=sealed,
    )
    if name in ("live_source_changed", "live_rubrics_changed"):
        with pytest.raises(ValueError, match="changed during evaluation"):
            harness_eval.run_harness_evaluation(**arguments)
        assert (program / "metrics.json").is_file()
        assert (program / "scientific_review_stdout.log").read_text() == "raw reviewer stdout\n"
        assert not _read(program / "evaluation_manifest.json").get("completed")
        return
    code = harness_eval.run_harness_evaluation(**arguments)
    assert code == (1 if name == "evaluation_failed" else 7 if name == "nonzero_correct" else 0)
    status = _read(program / "rubric_status.json")
    assert status == _read(experiment / "rubric_status.json")
    reviews = {row["id"]: row for row in status["rubrics"] if row["id"] in {"theory", "method"}}
    valid_review = name in ("PASS", "FAIL", "UNCERTAIN") or name.startswith("tamper_")
    accepted = name in ("PASS", "no_review", "sealed") or name.startswith("tamper_")
    assert status["overall_pass"] is accepted
    if name == "sealed":
        assert all(row["pass"] for row in reviews.values())
        assert _read(program / "evaluation_manifest.json")["producer"] == "sandbox_host_eval"
    else:
        for key, row in reviews.items():
            verdict = ("PASS" if key == "method" or name.startswith("tamper_") else name) if valid_review else None
            assert row["pass"] is (verdict == "PASS")
            assert row["assessment"] == (
                "passed" if verdict == "PASS" else "failed" if verdict == "FAIL" else "not_assessed"
            )
            assert "AI review, not proof" in row["evidence"]
            assert f"verdict={verdict or 'not_assessed'}" in row["evidence"]
            assert "source_contains" not in row["evidence"]
    no_invocation = name in {
        "no_python", "no_entrypoint", "no_model", "unconfigured", "no_review", "sealed",
        "incorrect", "truthy_correct", "evaluation_failed", "nonzero_correct", "launch_failure", "preexisting",
    }
    assert record_path.exists() is not no_invocation
    if not no_invocation:
        assert _read(record_path) == [{
            "argv": ["--stage", "review", "--program-dir", str(program), "--task-dir", str(experiment),
                     "--rubrics-file", str(task / "target_rubrics.json"),
                     "--model", environment["AI_STATISTICIAN_API_MODEL"]],
            "cwd": str(experiment),
        }]
        assert (program / "scientific_review_stdout.log").read_text() == "raw reviewer stdout\n"
        assert (program / "scientific_review_stderr.log").read_text() == "raw reviewer stderr\n"
    elif name != "launch_failure":
        assert not (program / "scientific_review_stdout.log").exists()
        assert not (program / "scientific_review_stderr.log").exists()
        assert not (program / "scientific_review.json").exists()
        assert not (program / ".scientific-review").exists()
        if name == "preexisting":
            assert (program / "scientific_review.md").read_text() == "Keep this pre-existing report unchanged\n"
        else:
            assert not (program / "scientific_review.md").exists()
    if name == "missing":
        assert not (program / "scientific_review.json").exists()
    if name != "evaluation_failed":
        assert _read(program / "metrics.json") == {"combined_score": 2}
        assert _read(program / "correct.json") == {"correct": correct}
        assert status["rubrics"][0]["pass"] is (name not in ("incorrect", "nonzero_correct"))
    if sealed is None:
        receipt = _read(program / "evaluation_manifest.json")
        expected_sources = {"src/program.py", "program_spec.toml", "input.bin"}
        if name == "preexisting":
            expected_sources.add("scientific_review.md")
        assert set(receipt["source_records"]) == expected_sources
        if name != "truthy_correct":
            evaluation = read_native_evaluation(
                program, requirements, attempt_id="review_attempt", idea_id="review_idea",
            )
            assert evaluation.complete is accepted
            if name != "evaluation_failed":
                assert evaluation.correct is correct and evaluation.score == 2
        for path in program.rglob("*"):
            if path.is_file() and path.relative_to(program).as_posix() not in expected_sources | {"evaluation_manifest.json"}:
                assert receipt["evidence_records"][path.relative_to(program).as_posix()] == hashlib.sha256(path.read_bytes()).hexdigest()
        if name.startswith("tamper_"):
            filename = {"summary": "scientific_review.json", "report": "scientific_review.md",
                        "session": ".scientific-review/session/result.json",
                        "stdout": "scientific_review_stdout.log", "stderr": "scientific_review_stderr.log"}[name[7:]]
            path = program / filename
            path.write_bytes(path.read_bytes() + b"\n")
            with pytest.raises(ValueError, match="stale native evaluation"):
                read_native_evaluation(program, requirements, attempt_id="review_attempt", idea_id="review_idea")
    before = _snapshot(experiment)
    with pytest.raises(SystemExit, match="agent-created evaluator artifact"):
        harness_eval.run_harness_evaluation(**arguments)
    assert _snapshot(experiment) == before
    assert not record_path.exists() or len(_read(record_path)) == 1


if __name__ == "__main__":
    import socket

    def no_network(*args, **kwargs):
        raise AssertionError("network is forbidden in deterministic campaign tests")

    socket.create_connection = no_network
    socket.socket.connect = no_network
    scenario, source, work = sys.argv[1:]
    sys.path.insert(0, source)
    _run_scenario(scenario, Path(work))
