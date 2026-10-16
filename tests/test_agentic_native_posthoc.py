"""Real upstream posthoc stages and product API transport, with no model calls."""

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import threading

import pytest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party/ai-scientist-v3"
PYTHON = UPSTREAM / ".venv/bin/python"
PIN = "2b8aa39285c35aaca3b0e06dd121061ef8a2d854"


@pytest.fixture(scope="module")
def upstream(tmp_path_factory):
    if not PYTHON.exists():
        pytest.skip("Pinned upstream environment is required")
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=UPSTREAM, text=True).strip() == PIN
    destination = tmp_path_factory.mktemp("native-posthoc")
    archive = subprocess.check_output(["git", "archive", PIN], cwd=UPSTREAM)
    with tarfile.open(fileobj=io.BytesIO(archive)) as sources:
        sources.extractall(destination, filter="data")
    for name in ("local_api_backend.patch", "native_campaign_semantics.patch", "native_posthoc.patch"):
        subprocess.run(["git", "apply", str(ROOT / "integrations/agentic-scientist" / name)], cwd=destination, check=True)
    return destination


SETUP = r'''
import hashlib, json, os, shutil, sys
from pathlib import Path
from src.investigation.harness_eval import run_harness_evaluation
from src.investigation.harness_incumbent import read_native_evaluation
from src.posthoc_pipeline.config import PosthocPipelineConfig
from src.posthoc_pipeline.pipeline import run_posthoc_pipeline
from src.posthoc_pipeline.cli import main as posthoc_main
root = Path(sys.argv[1])
scenario = sys.argv[2]
task, results, output = root / "task", root / "results", root / "report"
attempt = results / "ideas/attempt_1"
attempt.mkdir(parents=True)
task.mkdir()
spec = 'schema_version=1\ncode_root="src"\n[entrypoint]\npath="program.py"\nlanguage="python"\ntype="script"\n'
spec += '[copy]\nexclude=[]\ninclude=[]\n[integration]\nkind="generic"\nnotes=""\n'
for program in (task / "program_0", attempt / "program_1"):
    (program / "src").mkdir(parents=True)
    (program / "program_spec.toml").write_text(spec)
    (program / "src/program.py").write_text('VALUE = 17\n')
    (program / "src/theory.md").write_text('Unassessed opaque argument.\n')
rubrics = [{"id": "metric", "type": "metric", "metric": "combined_score", "operator": ">=", "threshold": 1}]
declaration = [{"path": "tables/arbitrary.csv", "kind": "table", "media_type": "text/csv"}]
for directory in (task, attempt):
    (directory / "task.md").write_text("Interpret the complete supplied results without repeating evaluation.")
    (directory / "target_rubrics.json").write_text(json.dumps(rubrics))
    (directory / "public_outputs.json").write_text(json.dumps(declaration))
evaluator = r"""import argparse, json, runpy
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--program_path')
p.add_argument('--results_dir')
a = p.parse_args()
out = Path(a.results_dir)
value = runpy.run_path(a.program_path)['VALUE']
count = Path('evaluation_count')
assert not count.exists(), 'consumed evaluator was called again'
count.write_text('1')
(out / 'metrics.json').write_text(json.dumps({'combined_score': value}))
(out / 'correct.json').write_text(json.dumps({'correct': True}))
(out / 'tables').mkdir()
(out / 'tables/arbitrary.csv').write_text('condition,value\na,17\nb,23\n')
(out / '.private').mkdir()
(out / '.private/review.json').write_text('PRIVATE CONTEXT MUST NOT BE EXPOSED')
"""
for directory in (task, attempt):
    (directory / "evaluate.py").write_text(evaluator)
program = attempt / "program_1"
if scenario == "missing_output":
    for directory in (task, attempt):
        (directory / "public_outputs.json").write_text(json.dumps([{"path": "missing.csv", "kind": "table"}]))
if scenario == "preexisting":
    (program / "tables").mkdir()
    (program / "tables/arbitrary.csv").write_text('author-forged results')
try:
    run_harness_evaluation(experiment_dir=attempt, attempt_id="attempt_1", idea_id="idea_1",
        rubrics_path=attempt / "target_rubrics.json", python_bin=sys.executable,
        global_memory_md=results / "memory.md", global_memory_jsonl=results / "memory.jsonl", timeout_seconds=30)
except (ValueError, FileNotFoundError):
    assert scenario in ("preexisting", "missing_output")
    assert (attempt / "evaluation_count").exists() == (scenario == "missing_output")
    assert not (program / "evaluation_manifest.json").exists() or not json.loads((program / "evaluation_manifest.json").read_text()).get("completed")
    print('EXPECTED_REJECTION')
    sys.exit(0)
if scenario == "changed_output":
    (program / "tables/arbitrary.csv").write_text('changed')
elif scenario == "changed_declaration":
    (attempt / "public_outputs.json").write_text('[]')
elif scenario == "changed_task":
    (attempt / "task.md").write_text('New question after evaluation')
if scenario.startswith("changed_"):
    try:
        read_native_evaluation(program, rubrics, attempt_id="attempt_1", idea_id="idea_1")
    except Exception:
        print('EXPECTED_REJECTION')
        sys.exit(0)
    raise AssertionError('Changed consumed evidence was accepted')
read_native_evaluation(program, rubrics, attempt_id="attempt_1", idea_id="idea_1")
before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in attempt.rglob('*') if p.is_file()}
(results / "best_program_manifest.json").write_text(json.dumps({"program_dir": str(program),
    "entrypoint_path": "src/program.py", "combined_score": 17, "correct": True, "source_attempt_id": "attempt_1"}))
generation = output / "generation"
generation.mkdir(parents=True)
candidate = {"id": "interpretation", "title": "Interpret supplied evidence", "family": "artifact_interpretation",
    "hypothesis": "Assess the existing observations without a predetermined conclusion",
    "relevance_reason": "Complete the report", "feasibility_reason": "Summaries already exist",
    "required_artifacts": ["evidence/tables/arbitrary.csv"], "requires_retrain": False,
    "implementation_plan": ["Read the supplied table and source, then report limitations"],
    "expected_claim": "Only what the observations support", "expected_outputs": ["analysis_summary.md"]}
(generation / "posthoc_bundle.json").write_text(json.dumps({"decision": "propose_analyses", "analyses": [candidate]}))
(generation / "posthoc_selection.json").write_text(json.dumps({"accepted": [{"id": "interpretation"}], "rejected": []}))
cfg = PosthocPipelineConfig()
cfg.agent.name, cfg.agent.model = "local-api", "pinned-fixture"
cfg.paths.task_dir, cfg.paths.results_dir, cfg.paths.output_dir = str(task), str(results), str(output)
cfg.container.enabled = False
cfg.execution.checkpoint_mode, cfg.execution.retrain_if_checkpoint_missing = "optional", False
cfg.execution.max_attempts_per_analysis = 1
cfg.execution.analysis_timeout_seconds = 30
assert posthoc_main(['--stages', '0,1,4,5,6', 'agent.name=local-api', 'agent.model=pinned-fixture',
    'paths.task_dir=' + str(task), 'paths.results_dir=' + str(results), 'paths.output_dir=' + str(output),
    'container.enabled=false', 'execution.checkpoint_mode=optional', 'execution.retrain_if_checkpoint_missing=false',
    'execution.max_attempts_per_analysis=1', 'execution.analysis_timeout_seconds=30']) == 0
assert (attempt / 'evaluation_count').read_text() == '1'
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == digest for p, digest in before.items())
staged = json.loads((output / '_extracted_bundle/evidence_manifest.json').read_text())
assert staged['source_role'] == 'completed_native_evaluation'
assert set(staged['files']) == {'evidence/tables/arbitrary.csv'}
if scenario == 'pipeline_gap':
    assert not (output / 'latest_manifest.json').exists()
    assert json.loads((output / 'ranking.json').read_text())['valid'] == []
else:
    latest = json.loads((output / 'latest_manifest.json').read_text())
    assert len(latest['valid_analyses']) == 1
    selected = Path(latest['valid_analyses'][0]['selected_attempt_dir'])
    assert '17 and 23' in (selected / 'analysis_summary.md').read_text()
    assert (selected / '.local-api/session/result.json').is_file()
try:
    run_posthoc_pipeline(cfg, stages={0, 1, 4, 5, 6})
except ValueError:
    pass
else:
    raise AssertionError('Consumed report workspace was reused')
print('VERIFIED_NATIVE_POSTHOC')
'''


@pytest.mark.parametrize("scenario", ["preexisting", "missing_output", "changed_output", "changed_declaration", "changed_task"])
def test_native_public_output_identity(upstream, tmp_path, scenario):
    result = subprocess.run([str(PYTHON), "-c", SETUP, str(tmp_path), scenario], cwd=upstream,
        text=True, capture_output=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EXPECTED_REJECTION" in result.stdout


@pytest.mark.parametrize("disposition", ["candidate", "gap"])
def test_native_posthoc_full_upstream_path_reads_table_via_real_api(upstream, tmp_path, disposition):
    requests = []
    report = "# Results\nThe supplied table contains 17 and 23. This fixture does not establish a scientific claim.\n"
    ids = ["analysis_summary_present", "analysis_manifest_present", "interestingness_rubric_present",
           "required_outputs_present", "claim_grounded", "checkpoint_guardrail_respected"]
    files = {
        "analysis_summary.md": report,
        "interestingness_rubric.json": json.dumps({"scope": "deterministic transport fixture"}),
        "analysis_manifest.json": json.dumps({"analysis_id": "interpretation", "attempt_id": "attempt_1",
            "summary": "Read supplied results", "claim": "Fixture only", "grounded": True,
            "reran_evaluator": False, "outputs": {"reports": ["analysis_summary.md"]},
            "evidence_paths": ["task_bundle/evidence/tables/arbitrary.csv"], "checkpoint_paths": []}),
        "rubric_status.json": json.dumps({"analysis_id": "interpretation", "overall_pass": True,
            "rubrics": [{"id": key, "pass": True, "evidence": "Fixture only"} for key in ids]}),
    }
    actions = [("read_file", {"path": "task_bundle/program_0/.private/review.json"}),
               ("read_file", {"path": "task_bundle/evidence/tables/arbitrary.csv"})]
    actions.extend(("write_file", {"path": path, "content": content, "expected_sha256": None}) for path, content in files.items())
    actions.append(("finish", {"disposition": disposition, "summary": "Report ready for independent review"}))

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            name, arguments = actions[len(requests) - 1]
            raw = {"model": "pinned-fixture", "choices": [{"finish_reason": "tool_calls", "message": {
                "role": "assistant", "content": "", "tool_calls": [{"id": str(len(requests)), "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)}}]}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}
            payload = json.dumps(raw).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    receipt = tmp_path / "deployment.json"
    receipt.write_text('"deterministic fixture, not a model"')
    config = tmp_path / "api-config.json"
    config.write_text(json.dumps({"model": "pinned-fixture", "base_url": f"http://127.0.0.1:{server.server_port}/v1",
        "max_tokens": 8192, "temperature": 1.0, "timeout_seconds": 10, "max_turns": 8,
        "deployment_ref": {"path": str(receipt), "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest()}}))
    environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(tmp_path),
        "TMPDIR": str(tmp_path), "AGENTIC_TEMP_ROOT": str(tmp_path),
        "AI_STATISTICIAN_API_PYTHON": sys.executable,
        "AI_STATISTICIAN_API_ENTRYPOINT": str(ROOT / "scripts/run_agentic_api.py"),
        "AI_STATISTICIAN_API_CONFIG": str(config)}
    try:
        result = subprocess.run([str(PYTHON), "-c", SETUP, str(tmp_path), "pipeline_gap" if disposition == "gap" else "pipeline"], cwd=upstream,
            env=environment, text=True, capture_output=True, timeout=60)
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERIFIED_NATIVE_POSTHOC" in result.stdout
    assert len(requests) == len(actions)
    messages = json.dumps(requests)
    assert "PRIVATE CONTEXT MUST NOT BE EXPOSED" not in messages
    assert "outside the stage's file grants" in messages
    assert "a,17" in messages and "b,23" in messages


@pytest.mark.parametrize("declaration", [[], {}, [{"path": "../x", "kind": "table"}],
    [{"path": ".private/x", "kind": "table"}], [{"path": "tables/*", "kind": "table"}],
    [{"path": "/tmp/x", "kind": "table"}], [{"path": "table.csv"}],
    [{"path": "x", "kind": "unknown"}], [{"path": "x", "kind": "table"}] * 2])
def test_native_output_declarations_use_explicit_artifact_paths(upstream, tmp_path, declaration):
    (tmp_path / "public_outputs.json").write_text(json.dumps(declaration))
    result = subprocess.run([str(PYTHON), "-c", """
from pathlib import Path
import sys
from src.investigation.harness_incumbent import native_public_outputs
try:
    native_public_outputs(Path(sys.argv[1]))
except ValueError:
    sys.exit(0)
raise AssertionError('Malformed output declaration accepted')
""", str(tmp_path)], cwd=upstream, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
