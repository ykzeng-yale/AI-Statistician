from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts.prepare_agentic_task import prepare_task


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party" / "ai-scientist-v3"
INTEGRATION = ROOT / "integrations" / "agentic-scientist"
PIN = "2b8aa39285c35aaca3b0e06dd121061ef8a2d854"


def test_local_configuration_has_no_cloud_provider_or_credential():
    config = json.loads((INTEGRATION / "opencode.local.json").read_text())
    assert config["enabled_providers"] == ["local-qwen"]
    assert set(config["provider"]) == {"local-qwen"}
    assert config["model"] == config["small_model"] == "local-qwen/Qwen3-4B-Instruct-2507"
    provider = config["provider"]["local-qwen"]
    assert provider["options"] == {"baseURL": "http://127.0.0.1:8081/v1"}
    assert "apiKey" not in str(config) and "/Users/" not in str(config)


def test_real_upstream_composes_statistical_profile_and_renders_prompts(tmp_path):
    executable = Path(os.environ.get("AI_STATISTICIAN_V3_PYTHON", UPSTREAM / ".venv/bin/python"))
    if not executable.is_file():
        pytest.skip("Initialize the pinned submodule and uv sync --frozen --no-dev for upstream conformance")
    pin = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    assert pin == PIN
    brief = tmp_path / "brief.md"
    brief.write_text("# Opaque question\nKeep this whole brief, including its heading.\n")
    task = prepare_task(brief, tmp_path / "task")
    auth = tmp_path / "empty-auth"
    auth.mkdir()
    script = r'''
import contextlib, io, json, os, re, socket
from pathlib import Path
from src.pipeline.cli import load_pipeline_config
from src.pipeline.config import parse_pipeline_phases, validate_pipeline_config
from src.pipeline.paths import derive_paths
from src.pipeline.phases import (build_task_drafting_cmd, build_investigation_cmd,
    build_ablations_cmd, build_final_cmd, build_posthoc_cmd, build_paper_cmd)
from src.investigation.files import read_task_sections, load_instructions, ensure_task_copy_in_results
from src.investigation.config_loader import load_config as load_investigation_config
from src.investigation.config import should_use_harness_instruction
from src.investigation.skill_scope import skills_for_step
from src.investigation.program_clone import clone_program_dir
from src.investigation.program_spec import render_default_program_spec_toml
root, task = Path(os.environ["AI_STATISTICIAN_ROOT"]), Path(os.environ["TEST_TASK"])
overrides = [
    "hydra.searchpath=[" + (root / "integrations/agentic-scientist/configs").as_uri() + "]",
    "preset=statistician", "task.dir=" + str(task),
    "paths.results_root=" + str(task.parent / "runs"), "run_id=opaque_test",
]
cfg = load_pipeline_config(overrides)
assert cfg.agent.name == "opencode" and cfg.agent.model == "local-qwen/Qwen3-4B-Instruct-2507"
assert cfg.container.enabled is True and cfg.container.env_file == "" and cfg.container.gpu_count == 0
assert cfg.container.auth_root == os.environ["AI_STATISTICIAN_AUTH_ROOT"]
assert parse_pipeline_phases(cfg.execution.phases) == {
    "task_drafting", "investigation", "ablations", "final_evaluation", "posthoc", "paper"}
assert cfg.paper.final_outcome_policy == "allow_not_qualified"
assert cfg.investigation.get("paper.ai_review") == "disabled"
assert cfg.investigation.get("execution.harness_evaluated_attempts") is True
assert "generate-concept-figure" not in cfg.paper.get("skills")
goal, rubric, _ = read_task_sections(task)
assert "Opaque question" in goal and "whole brief" in goal and "not mathematical proof" in rubric
paths = derive_paths(cfg)
commands = {name: build(cfg, paths) for name, build in (
    ("draft", build_task_drafting_cmd), ("investigation", build_investigation_cmd),
    ("ablations", build_ablations_cmd), ("final", build_final_cmd),
    ("posthoc", build_posthoc_cmd), ("paper", build_paper_cmd))}
for name, command in commands.items():
    assert "research-agent-runtime" not in " ".join(command)
    if name != "final":
        assert any("local-qwen/Qwen3-4B-Instruct-2507" in arg for arg in command)
# This unresolved upstream dependency must not be mistaken for full native execution.
assert "--container-image" in commands["final"]
investigation = load_investigation_config(commands["investigation"][3:])
assert investigation.execution.harness_evaluated_attempts is True
assert Path(investigation.paths.instruct) == Path(cfg.investigation.get("paths.instruct"))
assert should_use_harness_instruction(investigation) is False
assert skills_for_step("run_harness_eval") == ("edit-program", "memory-log")
native = load_pipeline_config(overrides + ["container.enabled=false"])
native_errors = validate_pipeline_config(native)
assert "task_drafting requires container.enabled=true" in native_errors
assert "final phase requires container.enabled=true" in native_errors
staged = ensure_task_copy_in_results(task, paths.investigation_workspace_dir)
for path in task.rglob("*"):
    if path.is_file():
        assert (staged / path.relative_to(task)).read_bytes() == path.read_bytes()
starter = task.parent / "clone_check/program_0"
(starter / "src/theory").mkdir(parents=True)
(starter / "diagnostics").mkdir()
(starter / "program_spec.toml").write_text(render_default_program_spec_toml())
for relative, text in {
    "src/program.py": "# Opaque executable fixture, not a statistical method.\n",
    "src/theory/argument.md": "# Opaque reviewable argument\nUnresolved step.\n",
    "src/theory/argument.tex": "% Opaque derivation fixture.\n",
    "diagnostics/observation.txt": "Exploratory observation, not proof.\n",
}.items():
    (starter / relative).write_text(text)
candidate = starter.parent / "program_1"
clone_program_dir(src_dir=starter, dst_dir=candidate)
for path in starter.rglob("*"):
    if path.is_file():
        assert (candidate / path.relative_to(starter)).read_bytes() == path.read_bytes()
prompt = load_instructions(Path(cfg.investigation.get("paths.instruct")), staged, paths.run_dir, {
    "ACTIVE_IDEA_JSON": "{}", "ACTIVE_RUBRICS_JSON": "[]",
    "ACTIVE_IDEA_FILE": "./active_idea.json", "ACTIVE_RUBRICS_FILE": "./active_rubrics.json",
    "ATTEMPT_ID": "opaque_attempt", "IDEA_ID": "opaque_idea",
    "MAX_PROGRAM_EVALS_PER_ATTEMPT": "1", "PUBLIC_SEARCH_CONTRACT_SECTION": "",
    "GLOBAL_MEMORY_MD_FILE": "./memory.md", "GLOBAL_MEMORY_JSONL_FILE": "./memory.jsonl",
    "GLOBAL_MEMORY_RECENT_SUMMARY": "No previous observations.",
})
assert "$TASK_SOURCE_DIR/resources/search/statistical-research/SKILL.md" in prompt
assert not re.search(r"\{\{[A-Z_]+\}\}", prompt)
assert "Do not invoke `evaluate.py`" in prompt and "host owns official" in prompt
assert "complete reviewable theory, algorithm and simulation project" in prompt
assert "There is no mandatory small-simulation stage" in prompt
assert "public task contract explicitly permits it" in prompt
assert "record it as not executed" in prompt
assert "Markdown/LaTeX" in prompt and "Lean is optional" in prompt
assert "Opaque question" in prompt and "{{TASK_GOAL}}" not in prompt
assert Path(cfg.paper.venue_file).is_file() and Path(cfg.paper.get("contributions_file")).is_file()
from src.pipeline import cli, phases
def forbidden(*args, **kwargs):
    raise AssertionError("dry run must not launch a process or open a network socket")
phases.subprocess.run = forbidden
socket.socket = forbidden
socket.create_connection = forbidden
output, errors = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
    exit_code = cli.main(overrides + ["--dry-run", "versioning.enabled=false"])
assert exit_code == 0, output.getvalue() + errors.getvalue()
print(json.dumps({"phases": list(commands), "native_final_adapter_complete": False,
                  "model_or_evaluator_calls": 0}))
'''
    result = subprocess.run([str(executable), "-c", script], cwd=UPSTREAM,
        env={**os.environ, "AI_STATISTICIAN_ROOT": str(ROOT), "TEST_TASK": str(task),
             "AGENTIC_TEMP_ROOT": str(tmp_path.resolve()), "AI_STATISTICIAN_AUTH_ROOT": str(auth)},
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["model_or_evaluator_calls"] == 0
    assert not list((task.parent / "runs").rglob("metrics.json"))
    assert (task / "resources/search/research_brief.md").read_bytes() == brief.read_bytes()


@pytest.mark.parametrize("language", ["python", "r"])
@pytest.mark.parametrize("failure", [False, True])
def test_real_native_handoff_executes_whole_project_without_certifying_theory(tmp_path, language, failure):
    """Exercise the existing executor with opaque files, not a statistical answer."""
    python = Path(os.environ.get("AI_STATISTICIAN_V3_PYTHON", UPSTREAM / ".venv/bin/python"))
    if not python.is_file():
        pytest.skip("Pinned upstream environment required for native execution conformance")
    runtime = str(python) if language == "python" else shutil.which("Rscript")
    if not runtime:
        pytest.skip("Native Rscript required for R execution conformance")
    assert subprocess.check_output(
        ["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip() == PIN
    source = tmp_path / "program_1/src"
    source.mkdir(parents=True)
    extension = "py" if language == "python" else "R"
    (source.parent / "program_spec.toml").write_text(
        f'schema_version = 1\ncode_root = "src"\n[entrypoint]\n'
        f'path = "program.{extension}"\nlanguage = "{language}"\ntype = "script"\n'
        '[copy]\nexclude = ["**/__pycache__/**"]\ninclude = []\n'
        '[integration]\nkind = "generic"\nnotes = "opaque execution fixture"\n')
    (source / "theory.md").write_text("# Opaque argument\nNot mathematically assessed.\n")
    (source / "protocol.txt").write_text("17\n")
    if language == "python":
        (source / "study.py").write_text(
            "import csv\nfrom pathlib import Path\n"
            "def run(destination):\n"
            "    count = int(Path('protocol.txt').read_text())\n"
            "    with open(destination, 'w') as output:\n"
            "        writer = csv.writer(output)\n"
            "        writer.writerow(['replication', 'marker'])\n"
            "        writer.writerows((i, 'opaque') for i in range(1, count + 1))\n"
            "    print('opaque study completed', flush=True)\n")
        (source / "program.py").write_text(
            "import sys\nfrom study import run\nrun(sys.argv[1])\n"
            + ("raise RuntimeError('opaque deliberate failure')\n" if failure else ""))
    else:
        (source / "study.R").write_text(
            "run <- function(destination) {\n"
            "  count <- scan('protocol.txt', quiet=TRUE)\n"
            "  write.csv(data.frame(replication=seq_len(count), marker='opaque'),\n"
            "            destination, row.names=FALSE)\n"
            "  cat('opaque study completed\\n')\n}\n")
        (source / "program.R").write_text(
            "source('study.R')\nrun(commandArgs(trailingOnly=TRUE)[1])\n"
            + ("stop('opaque deliberate failure')\n" if failure else ""))
    original = {p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()}
    evaluator = tmp_path / "evaluate.py"
    evaluator.write_text(
        "import argparse, csv, json, subprocess\nfrom pathlib import Path\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--program_path')\nparser.add_argument('--results_dir')\n"
        "args = parser.parse_args()\nsource = Path(args.program_path)\n"
        "output = Path(args.results_dir) / 'study_outputs'\noutput.mkdir()\n"
        f"command = {[runtime, *(['--vanilla'] if language == 'r' else [])]!r}\n"
        "result = subprocess.run(command + [str(source), str(output / 'replications.csv')],\n"
        "                        cwd=source.parent, check=False)\n"
        "if result.returncode:\n    raise SystemExit(result.returncode)\n"
        "with (output / 'replications.csv').open() as stream:\n"
        "    rows = list(csv.DictReader(stream))\n"
        "correct = len(rows) == 17 and all(row['marker'] == 'opaque' for row in rows)\n"
        "(Path(args.results_dir) / 'metrics.json').write_text(json.dumps(\n"
        "    {'combined_score': int(correct), 'completed_records': len(rows)}))\n"
        "(Path(args.results_dir) / 'correct.json').write_text(json.dumps(\n"
        "    {'correct': correct, 'scope': 'opaque execution fixture only'}))\n")
    (tmp_path / "rubrics.json").write_text(json.dumps([
        {"id": "executed", "type": "metric", "description": "completed_records >= 17",
         "verification": {"type": "metric", "metric": "completed_records", "op": ">=", "threshold": 17}},
        {"id": "argument", "type": "scientific_review", "description": "Assess the actual argument"},
    ]))
    before_evaluator = evaluator.read_bytes()
    home = tmp_path / "home"
    home.mkdir()
    environment = {"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
                   "LANG": "en_US.UTF-8"}
    command = [str(python), "-m", "src.investigation.harness_eval",
        "--experiment-dir", str(tmp_path), "--attempt-id", "opaque_attempt",
        "--idea-id", "opaque_idea", "--rubrics-file", str(tmp_path / "rubrics.json"),
        "--python-bin", str(python), "--global-memory-md", str(tmp_path / "memory.md"),
        "--global-memory-jsonl", str(tmp_path / "memory.jsonl"), "--timeout-seconds", "30"]
    result = subprocess.run(command, cwd=UPSTREAM, env=environment,
                            capture_output=True, text=True, timeout=60)
    candidate = source.parent
    assert (candidate / "evaluation_manifest.json").is_file(), result.stdout + result.stderr
    manifest = json.loads((candidate / "evaluation_manifest.json").read_text())
    status = json.loads((candidate / "rubric_status.json").read_text())
    assert manifest["attempt_id"] == "opaque_attempt"
    assert status["overall_pass"] is False  # Numeric execution cannot supply mathematical review.
    assert status["rubrics"][1]["pass"] is False
    assert "opaque study completed" in (candidate / "harness_evaluate_stdout.log").read_text()
    assert (candidate / "study_outputs/replications.csv").is_file()
    if failure:
        assert result.returncode != 0 and manifest["exit_code"] != 0
        assert "opaque deliberate failure" in (candidate / "harness_evaluate_stderr.log").read_text()
        assert all(row["assessment"] == "not_assessed" for row in status["rubrics"])
        assert not (candidate / "metrics.json").exists()
    else:
        assert result.returncode == manifest["exit_code"] == 0, result.stderr
        assert status["rubrics"][0]["pass"] is True
        assert status["rubrics"][1]["assessment"] == "failed"
        assert json.loads((candidate / "metrics.json").read_text())["completed_records"] == 17
    assert evaluator.read_bytes() == before_evaluator
    assert all((source / path).read_bytes() == data for path, data in original.items())
    preserved = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    refused = subprocess.run(command, cwd=UPSTREAM, env=environment,
                             capture_output=True, text=True, timeout=30)
    assert refused.returncode != 0 and "agent-created evaluator artifact is forbidden" in refused.stderr
    assert all((tmp_path / path).read_bytes() == data for path, data in preserved.items())
