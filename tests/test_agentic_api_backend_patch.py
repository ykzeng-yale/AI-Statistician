"""Mechanism tests only: patch pinned Sakana sources in temporary directories.

The executed launch/cleanup blocks are taken verbatim from the patched run.sh.
An inert executable records argv/cwd/environment; no model or evaluator runs.
Upstream source and LICENSE remain Sakana AI's Apache-2.0 material.
"""

from __future__ import annotations

import io
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import threading

import pytest


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party/ai-scientist-v3"
PATCH = ROOT / "integrations/agentic-scientist/local_api_backend.patch"
PIN = "2b8aa39285c35aaca3b0e06dd121061ef8a2d854"
RUN = "src/scripts/run.sh"
LEGACY_AGENTS = ("claude", "codex", "cursor", "opencode", "gemini", "pi")
COST_MESSAGE = (
    "local-api: skipping Headless cost parsing; "
    "native API receipts are not included in Headless totals."
)


def _run(command, *, cwd, env=None):
    return subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True, timeout=30,
    )


def _between(text, start, end):
    assert text.count(start) == 1
    assert text.count(end) == 1
    return text[text.index(start):text.index(end)]


@pytest.fixture(scope="module")
def upstream_copy(tmp_path_factory):
    if not (UPSTREAM / RUN).is_file():
        pytest.skip("Initialize the pinned ai-scientist-v3 submodule")
    pin = _run(["git", "rev-parse", "HEAD"], cwd=UPSTREAM)
    assert pin.returncode == 0 and pin.stdout.strip() == PIN
    archive = subprocess.check_output(["git", "archive", PIN], cwd=UPSTREAM)
    destination = tmp_path_factory.mktemp("local-api-upstream")
    with tarfile.open(fileobj=io.BytesIO(archive)) as sources:
        sources.extractall(destination, filter="data")
    return destination


@pytest.fixture(scope="module")
def patched(upstream_copy, tmp_path_factory):
    destination = tmp_path_factory.mktemp("local-api-patched")
    shutil.copytree(upstream_copy, destination, dirs_exist_ok=True)
    for args in (["--check"], []):
        result = _run(["git", "apply", *args, str(PATCH)], cwd=destination)
        assert result.returncode == 0, result.stdout + result.stderr
    return destination


@pytest.fixture
def fixture_env(tmp_path, patched):
    attempt = tmp_path / "attempt with spaces"
    attempt.mkdir()
    prompt = "Opaque instructions.\nQuotes: '\"; $(not-a-command)\n\nFinal line.\n"
    (attempt / "prompt.md").write_text(prompt)
    interpreter = tmp_path / "operator python ; literal"
    interpreter.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "keys = ('AI_STATISTICIAN_API_CONFIG', 'ATTEMPT_ID', 'TASK_SOURCE_DIR',\n"
        "        'API_SENTINEL', 'PATH', 'HOME', 'HEADLESS_MODELS_DEV_CACHE')\n"
        "record = {'argv': sys.argv[1:], 'cwd': str(Path.cwd()),\n"
        "          'env': {key: os.environ.get(key) for key in keys},\n"
        "          'prompt': Path('prompt.md').read_text()}\n"
        "Path(os.environ['API_RECORD']).write_text(json.dumps(record))\n"
        "print('{\"type\": \"native_api_receipt\", \"input_tokens\": 17}')\n"
        "sys.exit(int(os.environ.get('API_EXIT_CODE', '0')))\n"
    )
    interpreter.chmod(0o755)
    entrypoint = tmp_path / "entry point $(literal).py"
    entrypoint.write_text("# Not executed: the inert interpreter records this argument.\n")
    forbidden = tmp_path / "forbidden-headless"
    forbidden.write_text('#!/bin/sh\nprintf invoked > "$HEADLESS_MARKER"\nexit 97\n')
    forbidden.chmod(0o755)
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path),
        "PYTHONDONTWRITEBYTECODE": "1",
        "WRAPPER_PYTHON": sys.executable,
        "PYTHON_BIN": sys.executable,
        "REPO_ROOT": str(patched),
        "AGENT": "local-api",
        "AGENT_MODEL": "provider/pinned model ; $(literal) 'quoted'",
        "AGENT_PROFILE": "",
        "HARNESS_EVALUATED_ATTEMPT": "1",
        "AGENT_TIMEOUT_SECONDS": "",
        "CONTAINERIZE": "0",
        "CONTAINER_IMAGE": "unused",
        "CONTAINER_NETWORK": "unused",
        "CONTAINER_HOME_DIR": "",
        "CONTAINER_ENV_FILE": "",
        "EXPERIMENT_DIR": str(attempt),
        "RESULTS_DIR": str(tmp_path / "results"),
        "LOG_FILE": str(attempt / "agent.log"),
        "LOG_PIPE": str(attempt / "agent.fifo"),
        "AGENT_LOG_MAX_BYTES": "1048576",
        "PROMPT": "Do not substitute this variable for prompt.md",
        "TIMESTAMP": "fixture_timestamp",
        "INTERRUPTED": "0",
        "ATTEMPT_ID": "opaque_attempt_01",
        "TASK_SOURCE_DIR": str(tmp_path / "canonical task"),
        "AI_STATISTICIAN_API_PYTHON": str(interpreter),
        "AI_STATISTICIAN_API_ENTRYPOINT": str(entrypoint),
        "AI_STATISTICIAN_API_CONFIG": str(tmp_path / "pinned deployment.json"),
        "API_SENTINEL": "preserve spaces; $literal\nand newline",
        "API_RECORD": str(tmp_path / "invocation.json"),
        "COST_CALLS": str(tmp_path / "cost-calls.txt"),
        "HEADLESS_BIN": str(forbidden),
        "HEADLESS_MARKER": str(tmp_path / "headless-called"),
        "HEADLESS_MODELS_DEV_CACHE": "unchanged-for-local-api",
    }
    return env


def _launch(source, env, cwd):
    # Run the actual FIFO/logger/launch/wait/cost block, but stop before evaluation.
    script = (
        'source "$REPO_ROOT/src/scripts/lib/container_agent.sh"\n'
        'record_headless_cost_log() { printf "%s\\n" "$*" >> "$COST_CALLS"; }\n'
        + _between(source, 'mkfifo "$LOG_PIPE"', "# Reusable sessions belong")
        + '\nexit "$AGENT_EXIT_CODE"\n'
    )
    return _run(["bash", "-c", script], cwd=cwd, env=env)


def test_patch_scope_license_and_unchanged_research_handoff(upstream_copy, patched):
    changed = {
        str(path.relative_to(upstream_copy))
        for path in upstream_copy.rglob("*")
        if path.is_file() and path.read_bytes() != (patched / path.relative_to(upstream_copy)).read_bytes()
    }
    assert changed == {RUN, "src/investigation/config.py", "src/pipeline/config.py",
                       "src/scripts/idea.sh", "src/scripts/lib/container_agent.sh"}
    assert (patched / "LICENSE").read_bytes() == (upstream_copy / "LICENSE").read_bytes()
    assert PIN in PATCH.read_text() and "Apache-2.0" in PATCH.read_text()
    old, new = (upstream_copy / RUN).read_text(), (patched / RUN).read_text()
    # All embedded Python (staging, prompt rendering, manifests, output checks)
    # and the evaluator dispatch/terminal artifact checks are byte-identical.
    assert re.findall(r"<<'PY'\n(.*?)\nPY\n", old, re.S) == re.findall(
        r"<<'PY'\n(.*?)\nPY\n", new, re.S,
    )
    assert old[old.index("# Reusable sessions belong"):] == new[new.index("# Reusable sessions belong"):]
    clone = ('if [ "$AGENT" = "local-api" ]; then\n'
             '  (cd "$REPO_ROOT" && "$PYTHON_BIN" -m src.investigation.program_clone --from "$EXPERIMENT_DIR/program_0" --to "$EXPERIMENT_DIR/program_1")\n'
             'fi\n')
    assert new.count(clone) == 1
    assert _between(old, 'mkdir -p "$RESULTS_DIR"', 'case "$AGENT" in\n  claude)') == _between(
        new.replace(clone, "").replace('export AI_STATISTICIAN_CAMPAIGN_RESULTS="$RESULTS_DIR"\n', ""),
        'mkdir -p "$RESULTS_DIR"', 'case "$AGENT" in\n  claude)',
    )
    assert 'local-api) AGENT_CONFIG_DIR=".local-api" ;;' in new
    idea = (patched / "src/scripts/idea.sh").read_text()
    assert '\nexport TASK_SOURCE_DIR\n' in idea
    assert 'export TASK_SOURCE_DIR=' not in idea
    assert 'TASK_SOURCE_DIR="$IDEA_TASK_SOURCE_SHADOW"' in idea
    result = _run(["bash", "-n", str(patched / RUN)], cwd=patched)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("exit_code", [0, 23, 124, 130])
def test_actual_launch_delivers_exact_arguments_and_preserves_context(patched, fixture_env, tmp_path, exit_code):
    env = fixture_env | {"API_EXIT_CODE": str(exit_code)}
    result = _launch((patched / RUN).read_text(), env, tmp_path)
    assert result.returncode == exit_code, result.stdout + result.stderr
    record = json.loads(Path(env["API_RECORD"]).read_text())
    assert record["argv"] == [
        env["AI_STATISTICIAN_API_ENTRYPOINT"], "--prompt-file", "prompt.md",
        "--model", env["AGENT_MODEL"],
    ]
    assert record["cwd"] == str(Path(env["EXPERIMENT_DIR"]).resolve())
    assert record["prompt"] == (Path(env["EXPERIMENT_DIR"]) / "prompt.md").read_text()
    assert record["env"] == {key: env[key] for key in record["env"]}
    assert not Path(env["HEADLESS_MARKER"]).exists()
    assert not Path(env["COST_CALLS"]).exists()
    assert COST_MESSAGE in result.stderr
    assert "native_api_receipt" in Path(env["LOG_FILE"]).read_text()


@pytest.mark.parametrize("agent", LEGACY_AGENTS)
def test_legacy_launch_is_identical_to_pinned_upstream(upstream_copy, patched, fixture_env, tmp_path, agent):
    env = fixture_env | {
        "AGENT": agent, "HEADLESS_BIN": fixture_env["AI_STATISTICIAN_API_PYTHON"],
    }
    records = []
    for source in (upstream_copy, patched):
        Path(env["LOG_PIPE"]).unlink(missing_ok=True)
        Path(env["COST_CALLS"]).unlink(missing_ok=True)
        result = _launch((source / RUN).read_text(), env, tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr
        records.append((json.loads(Path(env["API_RECORD"]).read_text()), Path(env["COST_CALLS"]).read_text()))
        assert COST_MESSAGE not in result.stderr
    assert records[0] == records[1]
    assert records[1][0]["argv"][:6] == [agent, "--debug", "--usage", "--allow", "yolo", "--model"]
    assert f"attempt:opaque_attempt_01:fixture_timestamp completed" in records[1][1]


@pytest.mark.parametrize(
    ("extra", "harness", "message"),
    [
        (["--containerize"], True, "does not support --containerize"),
        ([], False, "requires --harness-evaluated-attempt"),
        (["--agent-profile", "profile"], True, "does not support --agent-profile/--profile"),
        (["--profile", ""], True, "does not support --agent-profile/--profile"),
        (["--reasoning-effort", "high"], True, "reasoning belongs to the pinned deployment"),
        (["--reasoning-effort", ""], True, "reasoning belongs to the pinned deployment"),
    ],
)
def test_actual_runner_rejects_unsupported_modes_before_launch(patched, fixture_env, tmp_path, extra, harness, message):
    command = ["bash", str(patched / RUN), "--agent", "local-api", "--model", "pinned"]
    if harness:
        command.append("--harness-evaluated-attempt")
    result = _run(command + extra, cwd=tmp_path, env=fixture_env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "local-api" in result.stderr and message in result.stderr
    assert not Path(fixture_env["API_RECORD"]).exists()
    assert not Path(fixture_env["HEADLESS_MARKER"]).exists()
    assert not Path(fixture_env["RESULTS_DIR"]).exists()


@pytest.mark.parametrize("model", [None, "", " \t", "none", "NULL"])
def test_local_api_requires_explicit_model(patched, fixture_env, tmp_path, model):
    command = ["bash", str(patched / RUN), "local-api", "--harness-evaluated-attempt"]
    if model is not None:
        command += ["--model", model]
    result = _run(command, cwd=tmp_path, env=fixture_env)
    assert result.returncode == 1
    assert "local-api requires an explicit --agent-model/--model" in result.stderr
    assert not Path(fixture_env["API_RECORD"]).exists()


@pytest.mark.parametrize("key", ["AI_STATISTICIAN_API_PYTHON", "AI_STATISTICIAN_API_ENTRYPOINT"])
@pytest.mark.parametrize("value", [None, "", "relative/path", "/missing/absolute/path"])
def test_operator_paths_fail_closed(patched, fixture_env, tmp_path, key, value):
    env = fixture_env.copy()
    env.pop(key)
    if value is not None:
        env[key] = value
    result = _run(
        ["bash", str(patched / RUN), "--agent", "local-api", "--model", "pinned",
         "--harness-evaluated-attempt"], cwd=tmp_path, env=env,
    )
    assert result.returncode == 1
    assert f"local-api requires {key}" in result.stderr
    assert not Path(env["API_RECORD"]).exists()


@pytest.mark.parametrize("agent", ["local-api", "opencode"])
def test_interrupted_cleanup_skips_only_local_api_cost_parser(patched, fixture_env, tmp_path, agent):
    env = fixture_env | {"AGENT": agent, "INTERRUPTED": "1", "FORCE_CLEANUP": "1"}
    Path(env["LOG_FILE"]).write_text('{"type":"native_api_receipt"}\n')
    script = (
        "set -euo pipefail\n"
        'record_headless_cost_log() { printf "%s\\n" "$*" >> "$COST_CALLS"; }\n'
        "cleanup_search_only_task_source() { :; }\n"
        "cleanup_contracted_container_env() { :; }\n"
        + _between((patched / RUN).read_text(), "cleanup_run_processes() {", "on_interrupt() {")
        + "cleanup_run_processes\n"
    )
    result = _run(["bash", "-c", script], cwd=tmp_path, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    if agent == "local-api":
        assert COST_MESSAGE in result.stderr
        assert not Path(env["COST_CALLS"]).exists()
    else:
        assert COST_MESSAGE not in result.stderr
        assert "interrupted" in Path(env["COST_CALLS"]).read_text()


def test_configuration_accepts_native_campaign_but_not_unintegrated_modes(patched, tmp_path):
    python = Path(os.environ.get("AI_STATISTICIAN_V3_PYTHON", UPSTREAM / ".venv/bin/python"))
    if not python.is_file():
        pytest.skip("Pinned upstream Python environment required for config validation")
    script = '''
import socket
import subprocess
from src.investigation.config import InvestigationConfig, ConfigValidationError, VALID_AGENTS, validate
from src.pipeline.cli import load_pipeline_config
from src.pipeline.config import validate_pipeline_config

def forbidden(*args, **kwargs):
    raise AssertionError("config validation must not launch processes or use the network")

socket.socket = forbidden
socket.create_connection = forbidden
subprocess.Popen = forbidden
assert VALID_AGENTS == ("claude", "codex", "cursor", "opencode", "gemini", "pi", "local-api")
valid = InvestigationConfig()
valid.agent.name = "local-api"
valid.agent.model = "pinned"
valid.container.enabled = False
valid.execution.harness_evaluated_attempts = True
validate(valid)
import copy
for selection in ("model", "pool", "models", "container", "harness", "paper", "draft", "workers", "reasoning"):
    cfg = copy.deepcopy(valid)
    if selection == "model":
        cfg.agent.model = None
    elif selection == "pool":
        cfg.agent.pool = ["codex", "local-api"]
    elif selection == "models":
        cfg.agent.models = {"local-api": "different"}
    elif selection == "container":
        cfg.container.enabled = True
    elif selection == "harness":
        cfg.execution.harness_evaluated_attempts = False
    elif selection == "paper":
        cfg.paper.enabled = True
    elif selection == "draft":
        cfg.execution.draft_task_if_missing = True
    elif selection == "workers":
        cfg.execution.workers = 2
    else:
        cfg.agent.reasoning_effort = "high"
    try:
        validate(cfg)
    except ConfigValidationError as exc:
        assert "local-api supports a native, single-model" in exc.message
    else:
        raise AssertionError("unsupported local-api mode accepted: " + selection)
for selection in ("pool", "models"):
    cfg = InvestigationConfig()
    if selection == "pool":
        cfg.agent.pool = ["codex", "local-api"]
    else:
        cfg.agent.models = {"local-api": "pinned"}
    try:
        validate(cfg)
    except ConfigValidationError as exc:
        assert "local-api supports a native, single-model" in exc.message
    else:
        raise AssertionError("local-api must not enter a mixed-host pool")
for phases in ("all", "investigation", "paper"):
    cfg = load_pipeline_config(["agent.name=local-api", "execution.phases=" + phases])
    errors = validate_pipeline_config(cfg)
    assert len(errors) == 1 and "full-pipeline orchestration is not supported" in errors[0]
print("campaign and pipeline boundaries verified without execution")
'''
    result = _run(
        [str(python), "-c", script], cwd=patched,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(tmp_path),
             "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("candidate_fails", [False, True])
def test_full_native_runner_reaches_product_api_and_host_evaluator(patched, tmp_path, candidate_fails):
    """Real process boundary with deterministic HTTP responses, no model inference."""
    python = Path(os.environ.get("AI_STATISTICIAN_V3_PYTHON", UPSTREAM / ".venv/bin/python"))
    bash = Path(os.environ.get("AI_STATISTICIAN_V3_BASH", shutil.which("bash") or "/bin/bash"))
    version = subprocess.check_output([str(bash), "-c", "printf '%s' \"${BASH_VERSINFO[0]}\""], text=True)
    if not python.is_file() or int(version) < 4:
        pytest.skip("Pinned upstream Python and Bash 4+ required for complete native runner")
    task, results = tmp_path / "task", tmp_path / "results"
    source = task / "program_0/src"
    source.mkdir(parents=True)
    (source / "program.py").write_text("raise NotImplementedError('unimplemented fixture')\n")
    (source.parent / "data").mkdir()
    (source.parent / "data/input.bin").write_bytes(b"\x00\xffopaque binary starter\x80")
    (source.parent / "metrics.json").write_text('{"combined_score":999}')
    spec = (UPSTREAM / "examples/circpack/program_0/program_spec.toml").read_text()
    (source.parent / "program_spec.toml").write_text(spec)
    shutil.copy2(UPSTREAM / "examples/circpack/capture.py", task / "capture.py")
    (task / "task.md").write_text("# Goal\nOpaque native handoff fixture.\n# Rubrics\nExecute the candidate.\n# Constraints\nNo scientific claim.\n")
    evaluator = task / "evaluate.py"
    evaluator.write_text(
        "import argparse, json, subprocess, sys\nfrom pathlib import Path\n"
        "p=argparse.ArgumentParser()\np.add_argument('--program_path')\np.add_argument('--results_dir')\n"
        "a=p.parse_args()\nresult=subprocess.run([sys.executable,a.program_path],capture_output=True,text=True)\n"
        "print(result.stdout,end='')\nprint(result.stderr,end='',file=sys.stderr)\n"
        "if result.returncode: raise SystemExit(result.returncode)\n"
        "correct=result.stdout.strip()=='opaque-native-17'\nout=Path(a.results_dir)\n"
        "(out/'metrics.json').write_text(json.dumps({'combined_score':int(correct)}))\n"
        "(out/'correct.json').write_text(json.dumps({'correct':correct}))\n")
    rubrics = tmp_path / "rubrics.json"
    rubrics.write_text(json.dumps([{"id": "execution", "type": "metric", "metric": "combined_score", "operator": ">=", "threshold": 1}]))
    idea = tmp_path / "idea.json"
    idea.write_text(json.dumps({"idea_id": "opaque", "title": "Mechanism fixture"}))
    receipt = tmp_path / "deployment.json"
    receipt.write_text('{"type":"deterministic-http-fixture-not-a-model"}')
    requests = []
    candidate = "raise RuntimeError('opaque candidate failure')\n" if candidate_fails else "print('opaque-native-17')\n"
    actions = [
        ("read_file", {"path": "evaluate.py"}),
        ("write_file", {"path": "program_1/src/program.py", "content": candidate,
                        "expected_sha256": hashlib.sha256((source / "program.py").read_bytes()).hexdigest()}),
        ("write_file", {"path": "program_1/src/theory.md", "content": "# Unassessed fixture argument\n", "expected_sha256": None}),
        ("write_file", {"path": "program_1/program_spec.toml", "content": spec,
                        "expected_sha256": hashlib.sha256(spec.encode()).hexdigest()}),
        ("finish", {"disposition": "candidate", "summary": "Hand off the opaque fixture."}),
    ]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
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
    config = tmp_path / "api-config.json"
    config.write_text(json.dumps({"model": "pinned-fixture", "base_url": f"http://127.0.0.1:{server.server_port}/v1",
        "max_tokens": 8192, "temperature": 1.0, "timeout_seconds": 30, "max_turns": 8,
        "deployment_ref": {"path": str(receipt), "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest()}}))
    environment = {"PATH": f"{bash.parent}:{python.parent}:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(tmp_path), "WRAPPER_PYTHON": str(python), "TMPDIR": str(tmp_path),
        "AI_STATISTICIAN_API_PYTHON": sys.executable,
        "AI_STATISTICIAN_API_ENTRYPOINT": str(ROOT / "scripts/run_agentic_api.py"),
        "AI_STATISTICIAN_API_CONFIG": str(config), "AGENTIC_TEMP_ROOT": str(tmp_path)}
    try:
        completed = subprocess.run([str(bash), str(patched / RUN), "--agent", "local-api",
            "--agent-model", "pinned-fixture", "--task-dir", str(task), "--results-dir", str(results),
            "--rubrics-file", str(rubrics), "--idea-file", str(idea), "--attempt-id", "opaque_api_attempt",
            "--idea-dir-name", "opaque", "--harness-evaluated-attempt", "--max-program-evals-per-attempt", "1",
            "--agent-timeout-seconds", "30", "--harness-evaluation-timeout-seconds", "30"],
            cwd=patched, env=environment, capture_output=True, text=True, timeout=60)
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    attempt = results / "ideas/opaque"
    assert (attempt / "program_1/evaluation_manifest.json").is_file(), completed.stdout + completed.stderr
    assert len(requests) == 5
    assert requests[1]["messages"][-1]["role"] == "tool"
    assert "outside the stage's file grants" in requests[1]["messages"][-1]["content"]
    assert (attempt / "program_1/src/program.py").read_text() == candidate
    assert (attempt / "program_1/data/input.bin").read_bytes() == b"\x00\xffopaque binary starter\x80"
    assert not (attempt / "program_0/metrics.json").exists()
    assert (attempt / "evaluate.py").read_bytes() == evaluator.read_bytes()
    record = json.loads((attempt / ".local-api/session/result.json").read_text())
    assert record["terminal_payload"]["scientific_acceptance"] is False
    assert record["provider_usage"]["total_tokens"] == 75
    assert COST_MESSAGE in completed.stderr
    manifest = json.loads((attempt / "program_1/evaluation_manifest.json").read_text())
    if candidate_fails:
        assert completed.returncode != 0 and manifest["exit_code"] != 0
        assert "opaque candidate failure" in (attempt / "program_1/harness_evaluate_stderr.log").read_text()
        assert not (attempt / "program_1/metrics.json").exists()
    else:
        assert completed.returncode == manifest["exit_code"] == 0, completed.stdout + completed.stderr
        assert json.loads((attempt / "program_1/rubric_status.json").read_text())["overall_pass"] is True
