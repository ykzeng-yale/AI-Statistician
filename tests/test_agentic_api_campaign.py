"""Actual upstream campaign with opaque HTTP fixtures, never scientific evidence."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading

import pytest

from test_agentic_api_backend_patch import ROOT, UPSTREAM, patched, upstream_copy


@pytest.mark.parametrize("failure_kind,route,iterative", [
    ("execution", "investigation", False), ("artifact_execution", "investigation", False),
    ("review", "investigation", False), ("review", "pipeline", False),
    ("execution", "investigation", True),
    ("artifact_execution", "investigation", True), ("review", "investigation", True),
    ("review", "pipeline", True),
])
def test_native_api_campaign_revises_after_actual_host_failure(patched, tmp_path, failure_kind, route, iterative):
    python = Path(os.environ.get("AI_STATISTICIAN_V3_PYTHON", UPSTREAM / ".venv/bin/python"))
    bash = Path(os.environ.get("AI_STATISTICIAN_V3_BASH", shutil.which("bash") or "/bin/bash"))
    version = subprocess.check_output([str(bash), "-c", "printf '%s' \"${BASH_VERSINFO[0]}\""], text=True)
    if not python.is_file() or int(version) < 4:
        pytest.skip("Pinned upstream Python and Bash 4+ required for native campaign")
    checkout = tmp_path / "upstream"
    shutil.copytree(patched, checkout)
    subprocess.run(["git", "apply", str(ROOT / "integrations/agentic-scientist/native_campaign_semantics.patch")],
                   cwd=checkout, check=True, capture_output=True)
    subprocess.run(["git", "apply", str(ROOT / "integrations/agentic-scientist/native_posthoc.patch")],
                   cwd=checkout, check=True, capture_output=True)
    if iterative:
        subprocess.run(["git", "apply", str(ROOT / "integrations/agentic-scientist/native_iteration.patch")],
                       cwd=checkout, check=True, capture_output=True)
    task = tmp_path / "task"
    results = tmp_path / "envelope/investigation" if route == "pipeline" else tmp_path / "results"
    initial = "raise NotImplementedError('unimplemented fixture')\n"
    (task / "program_0/src").mkdir(parents=True)
    (task / "program_0/src/program.py").write_text(initial)
    shutil.copy2(UPSTREAM / "examples/circpack/program_0/program_spec.toml", task / "program_0/program_spec.toml")
    shutil.copy2(UPSTREAM / "examples/circpack/capture.py", task / "capture.py")
    (task / "task.md").write_text("# Goal\nOpaque complete-candidate fixture.\n# Rubrics\nMeet the fixed host criterion.\n# Constraints\nNo scientific claim.\n")
    fixed = [{"id": "execution", "type": "metric", "description": "combined_score >= 1",
              "metric": "combined_score", "operator": ">=", "threshold": 1}]
    if failure_kind == "review":
        fixed.append({"id": "argument", "type": "review", "description": "Opaque independent review fixture."})
    (task / "target_rubrics.json").write_text(json.dumps(fixed))
    if iterative and failure_kind == "execution":
        (task / "public_outputs.json").write_text(json.dumps([{"path": "never_produced.json", "kind": "derived"}]))
    if route == "pipeline":
        (task / "public_outputs.json").write_text(json.dumps([{"path": "metrics.json", "kind": "table"}]))
        plan = task / "posthoc"
        plan.mkdir()
        (plan / "posthoc_bundle.json").write_text(json.dumps({"decision": "propose_analyses", "analyses": [{
            "id": "interpretation", "title": "Interpret opaque observations", "family": "fixture",
            "requires_retrain": False, "expected_outputs": ["analysis_summary.md"],
            "expected_claim": "No scientific claim; interpret the actual fixture outcome."}]}))
        (plan / "posthoc_selection.json").write_text(json.dumps({"accepted": [{"id": "interpretation"}], "rejected": []}))
    evaluator = task / "evaluate.py"
    evaluator.write_text(
        "import argparse, json, os, subprocess, sys\nfrom pathlib import Path\n"
        "p=argparse.ArgumentParser()\np.add_argument('--program_path')\np.add_argument('--results_dir')\n"
        "a=p.parse_args()\nr=subprocess.run([sys.executable,a.program_path],capture_output=True,text=True)\n"
        "print(r.stdout,end='')\nprint(r.stderr,end='',file=sys.stderr)\n"
        "if r.returncode: raise SystemExit(r.returncode)\n"
        "correct=r.stdout.strip()=='opaque-native-17'\nout=Path(a.results_dir)\n"
        "(out/'evaluation_budget.txt').write_text(os.environ.get('EVALUATION_TIMEOUT_SECONDS','unset'))\n"
        "(out/'metrics.json').write_text(json.dumps({'combined_score':int(correct)}))\n"
        "(out/'correct.json').write_text(json.dumps({'correct':correct}))\n"
        "(out/'never_produced.json').write_text('{}')\n")
    if failure_kind == "artifact_execution":
        (task / "public_outputs.json").write_text(json.dumps([
            {"path": "execution_observation.json", "kind": "derived"}]))
        evaluator.write_text(
            "import argparse, json, os, subprocess, sys\nfrom pathlib import Path\n"
            "p=argparse.ArgumentParser()\np.add_argument('--program_path')\np.add_argument('--results_dir')\n"
            "a=p.parse_args()\nr=subprocess.run([sys.executable,a.program_path],capture_output=True,text=True)\n"
            "out=Path(a.results_dir)\ncorrect=r.returncode==0 and r.stdout.strip()=='opaque-native-17'\n"
            "(out/'evaluation_budget.txt').write_text(os.environ.get('EVALUATION_TIMEOUT_SECONDS','unset'))\n"
            "assert not (out/'private_observation.json').exists(), 'Old evaluator result was cloned'\n"
            "(out/'execution_observation.json').write_text(json.dumps({'stdout':r.stdout,'stderr':r.stderr,'returncode':r.returncode}))\n"
            "(out/'private_observation.json').write_text('undeclared private result')\n"
            "(out/'metrics.json').write_text(json.dumps({'combined_score':int(correct)}))\n"
            "(out/'correct.json').write_text(json.dumps({'correct':correct}))\n")
    requests, actions = [], []
    failure_file = "harness_evaluate_stderr.log" if failure_kind == "execution" else "scientific_review.md"
    if failure_kind == "artifact_execution":
        failure_file = "execution_observation.json"
    failure_path = ("program_1/" if iterative else "history/ideas/01_first_attempt/program_1/") + failure_file
    previous_candidate = initial
    for cycle, title in ((1, "First attempt"), (2, "Second attempt")):
        proposed = [{"id": "weakened", "type": "metric", "description": "combined_score >= 0"},
                    {"id": "marker", "type": "implementation", "description": "Include a fixture marker",
                     "verification": {"type": "source_contains", "patterns": ["opaque"]}}]
        bundle = {"idea_id": f"opaque_{cycle}", "title": title, "hypothesis": "Opaque mechanism fixture",
                  "implementation_plan": ["Author a source file"], "target_rubrics": proposed,
                  "notes_for_agent": "No scientific claim."}
        if cycle == 2 and not iterative:
            actions.append(("read_file", {"path": failure_path}))
        if not iterative or cycle == 1:
            actions.extend([
                ("write_file", {"path": "idea_bundle.json", "content": json.dumps(bundle), "expected_sha256": None}),
                ("write_file", {"path": "target_rubrics.json", "content": json.dumps(proposed), "expected_sha256": None}),
                ("finish", {"disposition": "candidate", "summary": "Idea handoff."}),
            ])
        if cycle == 2:
            actions.append(("read_file", {"path": failure_path}))
            if iterative:
                actions.append(("clone_program", {}))
        if iterative and cycle == 1:
            spec = (task / "program_0/program_spec.toml").read_text()
            actions.extend([
                ("remove_file", {"path": "program_1/program_spec.toml", "expected_sha256": hashlib.sha256(spec.encode()).hexdigest()}),
                ("evaluate_program", {}),
                ("write_file", {"path": "program_1/program_spec.toml", "content": spec, "expected_sha256": None}),
            ])
        candidate = "raise RuntimeError('opaque feedback 19')\n" if cycle == 1 and failure_kind in {"execution", "artifact_execution"} else "print('opaque-native-17')\n"
        program = f"program_{cycle}" if iterative else "program_1"
        actions.extend([
            ("write_file", {"path": program + "/src/program.py", "content": candidate,
                            "expected_sha256": hashlib.sha256((previous_candidate if iterative else initial).encode()).hexdigest()}),
            ("write_file", {"path": program + "/src/theory.md", "content": f"# Unassessed fixture version {cycle}\n",
                "expected_sha256": hashlib.sha256(b"# Unassessed fixture version 1\n").hexdigest() if iterative and cycle == 2 else None}),
        ])
        previous_candidate = candidate
        actions.append(("evaluate_program", {}) if iterative else
            ("finish", {"disposition": "candidate", "summary": "Research handoff, not accepted science."}))
        if failure_kind == "review":
            actions.extend([
                ("read_file", {"path": "candidate/src/theory.md"}),
                ("write_file", {"path": "review.md", "content": "# Opaque review\nopaque feedback 19\n", "expected_sha256": None}),
                ("submit_review", {"verdicts": [{"id": "argument", "status": "FAIL" if cycle == 1 else "PASS"}]}),
            ])
        if iterative:
            if cycle == 1:
                if failure_kind == "review":
                    actions.append(("read_file", {"path": "program_1/scientific_review_stderr.log"}))
                actions.extend([
                    ("evaluate_program", {}),
                    ("write_file", {"path": "program_1/src/program.py", "content": "overwritten consumed source",
                                    "expected_sha256": hashlib.sha256(candidate.encode()).hexdigest()}),
                    ("write_file", {"path": "program_2/src/forbidden.py", "content": "uncloned future source", "expected_sha256": None}),
                    ("read_file", {"path": "program_1/private_observation.json"}),
                    ("list_files", {"prefix": "program_1/src/"}),
                ])
            else:
                actions.extend([
                    ("clone_program", {}),
                    ("finish", {"disposition": "candidate", "summary": "Evaluated fixture, not accepted science."}),
                ])
    if route == "pipeline":
        ids = ["analysis_summary_present", "analysis_manifest_present", "interestingness_rubric_present",
               "required_outputs_present", "claim_grounded", "checkpoint_guardrail_respected"]
        reports = {
            "analysis_summary.md": "# Opaque fixture\nThe selected result is 1. The public review remains AI feedback, not proof.\n",
            "interestingness_rubric.json": json.dumps({"scope": "Fixture only"}),
            "analysis_manifest.json": json.dumps({"analysis_id": "interpretation", "attempt_id": "attempt_1",
                "summary": "Interpret fixture", "claim": "No scientific claim", "grounded": True,
                "reran_evaluator": False, "outputs": {"reports": ["analysis_summary.md"]},
                "evidence_paths": ["task_bundle/evidence/metrics.json"], "checkpoint_paths": []}),
            "rubric_status.json": json.dumps({"analysis_id": "interpretation", "overall_pass": True,
                "rubrics": [{"id": key, "pass": True, "evidence": "Fixture only"} for key in ids]}),
        }
        actions.extend([
            ("read_file", {"path": "task_bundle/evidence/metrics.json"}),
            ("read_file", {"path": "task_bundle/program_0/scientific_review.md"}),
            *(("write_file", {"path": path, "content": content, "expected_sha256": None}) for path, content in reports.items()),
            ("finish", {"disposition": "candidate", "summary": "Fixture report ready"}),
        ])

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            if len(requests) > len(actions):
                self.send_error(500, "Unexpected extra model request")
                return
            name, args = actions[len(requests) - 1]
            response = {"model": "pinned-fixture", "choices": [{"finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": "", "tool_calls": [{"id": str(len(requests)), "type": "function",
                    "function": {"name": name, "arguments": json.dumps(args)}}]}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}
            payload = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    receipt = tmp_path / "deployment.json"
    receipt.write_text('{"type":"deterministic-http-fixture-not-a-model"}')
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config = tmp_path / "api-config.json"
    config.write_text(json.dumps({"model": "pinned-fixture", "base_url": f"http://127.0.0.1:{server.server_port}/v1",
        "max_tokens": 8192, "temperature": 1.0, "timeout_seconds": 30, "max_turns": 30 if iterative else 8,
        "deployment_ref": {"path": str(receipt), "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest()}}))
    environment = {"PATH": f"{bash.parent}:{python.parent}:/usr/bin:/bin:/usr/sbin:/sbin", "HOME": str(tmp_path),
        "WRAPPER_PYTHON": str(python), "TMPDIR": str(tmp_path), "AI_STATISTICIAN_API_PYTHON": sys.executable,
        "AI_STATISTICIAN_API_ENTRYPOINT": str(ROOT / "scripts/run_agentic_api.py"),
        "AI_STATISTICIAN_API_CONFIG": str(config), "AGENTIC_TEMP_ROOT": str(tmp_path)}
    try:
        harness_mode = "false" if iterative else "true"
        command = [str(python), "-m", "src.investigation.cli", "agent.name=local-api",
            "agent.model=pinned-fixture", "paths.task_dir=" + str(task), "paths.results_dir=" + str(results),
            "execution.harness_evaluated_attempts=" + harness_mode, "execution.max_idea_cycles=3",
            "execution.max_program_evals_per_attempt=3",
            "execution.max_idea_generation_attempts=1", "execution.run_timeout_seconds=30",
            "execution.idea_timeout_seconds=30", "execution.harness_evaluation_timeout_seconds=30",
            "versioning.enabled=false", "paper.enabled=false", "container.enabled=false"]
        if route == "pipeline":
            command = [str(python), "-m", "src.pipeline.cli", "agent.name=local-api", "agent.model=pinned-fixture",
                "task.dir=" + str(task), "paths.run_dir=" + str(tmp_path / "envelope"),
                "execution.phases=investigation,posthoc", "investigation.execution.harness_evaluated_attempts=" + harness_mode,
                "investigation.execution.max_program_evals_per_attempt=3",
                "investigation.execution.max_idea_cycles=3", "investigation.execution.max_idea_generation_attempts=1",
                "investigation.execution.run_timeout_seconds=30", "investigation.execution.idea_timeout_seconds=30",
                "investigation.execution.harness_evaluation_timeout_seconds=30", "versioning.enabled=false", "container.enabled=false",
                "posthoc.execution.max_attempts_per_analysis=1", "posthoc.execution.analysis_timeout_seconds=30"]
        run = subprocess.run(command,
            cwd=checkout, env=environment, capture_output=True, text=True, timeout=90)
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    assert run.returncode == 0, run.stdout + run.stderr
    assert len(requests) == len(actions), run.stdout + run.stderr
    idea_system = requests[0]["messages"][0]
    assert idea_system["role"] == "system"
    assert "the host owns global memory bookkeeping" in idea_system["content"]
    assert "operator's fixed acceptance contract" in idea_system["content"]
    assert not requests[0]["messages"][1]["content"].startswith("Native API stage contract:")
    first = results / "ideas/01_first_attempt"
    second = first if iterative else results / "ideas/02_second_attempt"
    first_program = first / "program_1"
    second_program = second / ("program_2" if iterative else "program_1")
    assert "opaque feedback 19" in (first / "program_1" / failure_file).read_text()
    if failure_kind == "execution":
        assert not (first / "program_1/metrics.json").exists()
    elif failure_kind == "artifact_execution":
        assert json.loads((first / "program_1/metrics.json").read_text())["combined_score"] == 0
        assert (first / "program_1/harness_evaluate_stderr.log").read_text() == ""
        assert json.loads((first / "program_1/rubric_status.json").read_text())["overall_pass"] is False
        assert not (first / "program_1/scientific_review.json").exists()
    else:
        assert json.loads((first / "program_1/metrics.json").read_text())["combined_score"] == 1
        assert json.loads((first / "program_1/rubric_status.json").read_text())["overall_pass"] is False
        assert (first_program / "src/theory.md").read_bytes() != (second_program / "src/theory.md").read_bytes()
        review_requests = [request for request in requests if "independently review" in request["messages"][0]["content"]]
        assert len(review_requests) == 6
        assert all("history/" not in request["messages"][0]["content"] for request in review_requests)
        assert "not proof" in json.loads((second_program / "scientific_review.json").read_text())["scope"]
    assert json.loads((second_program / "rubric_status.json").read_text())["overall_pass"] is True
    assert json.loads((second / "active_rubrics.json").read_text()) == fixed
    assert any("opaque feedback 19" in str(request["messages"][-1]) for request in requests)
    assert len(list((results / "ideas").iterdir())) == (1 if iterative else 2)
    best = json.loads((results / "best_program_manifest.json").read_text())
    assert best["correct"] is True and Path(best["program_dir"]) == second_program
    if iterative:
        assert (second_program / "evaluation_budget.txt").read_text() == "30"
        assert not (first / "program_3").exists()
        assert not (second_program / "src/forbidden.py").exists()
        author_requests = [r for r in requests if "complete research candidate" in r["messages"][0]["content"]]
        assert len(author_requests) > 10
        observations = [json.loads(json.loads(m["content"])["content"])
                        for m in author_requests[-1]["messages"] if m["role"] == "tool"]
        assert any("evaluation was consumed" in str(o) for o in observations)
        assert any("valid program_spec.toml" in str(o) for o in observations)
        assert sum("Edit only the current unevaluated candidate" in str(o) for o in observations) == 2
        assert any("already passes all rubrics" in str(o) for o in observations)
        assert any("outside the stage" in str(o) for o in observations)
        assert any(o.get("files") and all(not row["writable"] for row in o["files"]) for o in observations)
        assert (first_program / "src/program.py").read_text() == ("raise RuntimeError('opaque feedback 19')\n" if failure_kind in {"execution", "artifact_execution"} else "print('opaque-native-17')\n")
        for index in (1, 2):
            assert json.loads((first / f"program_{index}/evaluation_manifest.json").read_text())["program_id"] == f"program_{index}"
        verification = subprocess.run([sys.executable, "-c", r'''
import json, sys
from pathlib import Path
from ai_statistician.agentic_program_workspace import ProgramWorkspace
from ai_statistician.agentic_api_workspace import FileGrant
from ai_statistician.client_tool_loop import ClientToolInputError
from src.investigation.harness_incumbent import validate_fixed_campaign_resume
task, results, experiment, fresh = map(Path, sys.argv[1:])
task = Path(json.loads((results / "outer_state.json").read_text())["fixed_requirements"]["task_dir"])
criteria = json.loads((task / "target_rubrics.json").read_text())
def validate():
    return validate_fixed_campaign_resume(task_dir=task, results_dir=results,
        seed_program_dir=task / "program_0", target_rubrics=criteria, resume=True)
validate()
for path in (experiment / "program_1/src/program.py", experiment / "program_1/harness_evaluate_stderr.log",
             experiment / "program_1/evaluation_manifest.json", experiment / "rubric_status.json"):
    original = path.read_bytes()
    if path == experiment / "rubric_status.json":
        path.write_text(json.dumps({**json.loads(original), "tampered": True}))
    else:
        path.write_bytes(original + b"\n")
    try:
        try:
            validate()
        except ValueError:
            pass
        else:
            raise AssertionError("Altered consumed evidence was accepted: " + str(path))
    finally:
        path.write_bytes(original)
validate()
fresh.mkdir()
(fresh / "program_0").mkdir()
(fresh / "program_0/evaluation_manifest.json").write_text('{"fixture_readonly_baseline": true}')
(fresh / "program_1/src").mkdir(parents=True)
(fresh / "program_1/program_spec.toml").write_bytes((task / "program_0/program_spec.toml").read_bytes())
(fresh / "program_1/src/program.py").write_text("print('not the reference')\n")
for name in ("task.md", "target_rubrics.json", "evaluate.py"):
    (fresh / name).write_bytes((task / name).read_bytes())
(fresh / "active_rubrics.json").write_text(json.dumps(criteria[:1]))
arguments = dict(experiment=fresh, max_evaluations=1, timeout_seconds=5,
    attempt_id="budget_fixture", idea_id="budget_fixture", memory_md=fresh / "memory.md",
    memory_jsonl=fresh / "memory.jsonl", python_executable=sys.executable)
workspace = ProgramWorkspace((FileGrant("task.md", fresh / "task.md"),), **arguments)
try:
    workspace._execute("finish", {"disposition": "candidate", "summary": "Not yet evaluated"})
except ClientToolInputError:
    pass
else:
    raise AssertionError("Unevaluated handoff accepted")
workspace._execute("evaluate_program", {})
for action in ("evaluate_program", "clone_program"):
    try:
        workspace._execute(action, {})
    except ClientToolInputError:
        pass
    else:
        raise AssertionError("Consumed/capped evaluation was repeated")
assert workspace._execute("finish", {"disposition": "gap", "summary": "Unresolved fixture"}).terminal
try:
    ProgramWorkspace((FileGrant("task.md", fresh / "task.md"),), **arguments)
except FileExistsError:
    pass
else:
    raise AssertionError("Consumed author session was restarted")
''', str(task), str(results), str(first), str(tmp_path / "budget-fixture")], cwd=checkout,
            env={**environment, "PYTHONPATH": str(checkout) + os.pathsep + str(ROOT)},
            text=True, capture_output=True, timeout=20)
        assert verification.returncode == 0, verification.stdout + verification.stderr
    assert (task / "program_0/src/program.py").read_text() == initial
    assert (second / "evaluate.py").read_bytes() == evaluator.read_bytes()
    if route == "pipeline":
        posthoc = tmp_path / "envelope/posthoc"
        assert json.loads((posthoc / "integration_status.json").read_text())["status"] == "completed"
        report = json.loads((posthoc / "latest_manifest.json").read_text())["valid_analyses"][0]
        assert "selected result is 1" in Path(report["analysis_summary_path"]).read_text()
        assert "not proof" in json.loads((second_program / "scientific_review.json").read_text())["scope"]
