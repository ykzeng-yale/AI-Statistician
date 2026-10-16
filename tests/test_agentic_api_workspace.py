from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import signal
import sys
import time

import pytest

from ai_statistician.agentic_api_workspace import FileAuthorWorkspace, FileGrant, run_file_session
from ai_statistician.client_tool_loop import ClientToolExecutionContext, ClientToolInputError, ClientToolLoopError
from ai_statistician.model_backend import ClientToolCall, ClientToolTurnResponse
from ai_statistician.fingerprint import stable_hash
from scripts.run_agentic_api import load_config, posthoc_workspace, stage_workspace


CONTEXT = ClientToolExecutionContext(turn_index=0, call_index=0, calls_in_turn=1, total_calls_before=0)


def invoke(workspace, name, **args):
    return workspace.execute(ClientToolCall(call_id="fixture", name=name, input=args), CONTEXT)


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "public").mkdir()
    (tmp_path / "public/brief.md").write_text("Opaque brief.\nNo expected scientific answer.\n")
    (tmp_path / "private.txt").write_text("Evaluator-owned hidden fixture")
    return FileAuthorWorkspace((
        FileGrant("sources", tmp_path / "public", directory=True),
        FileGrant("candidate/src", tmp_path / "candidate/src", directory=True, writable=True),
        FileGrant("candidate/program_spec.toml", tmp_path / "candidate/program_spec.toml", writable=True),
    ))


def test_file_reads_are_paginated_and_hashed(workspace):
    result = invoke(workspace, "read_file", path="sources/brief.md", offset=0, limit=7)
    assert result.content["content"] == "Opaque "
    assert result.content["next_offset"] == 7
    assert result.content["sha256"] == sha("Opaque brief.\nNo expected scientific answer.\n")
    search = invoke(workspace, "search_file", path="sources/brief.md", query="scientific")
    assert search.content["matches"] == [{"line": 2, "text": "No expected scientific answer."}]
    catalog = invoke(workspace, "list_files", prefix="sources", limit=1).content
    assert catalog["files"][0]["writable"] is False
    assert catalog["next_offset"] is None


@pytest.mark.parametrize("path", ["../private.txt", "sources/../private.txt", "/etc/passwd", "private.txt", "sources//brief.md"])
def test_unauthorized_or_noncanonical_reads_return_observations(workspace, path):
    result = invoke(workspace, "read_file", path=path)
    assert result.is_error
    assert "Evaluator-owned hidden fixture" not in str(result.content)


def test_model_authors_exact_changes_and_stale_edits_are_not_repaired(workspace, tmp_path):
    original = "# Claim\nAn unresolved step remains.\n"
    created = invoke(workspace, "write_file", path="candidate/src/theory.md", content=original, expected_sha256=None)
    assert created.state_changed
    stale = invoke(workspace, "edit_file", path="candidate/src/theory.md", expected_sha256="0" * 64,
        edits=[{"old_text": "unresolved", "new_text": "revised"}])
    assert stale.is_error and "hash changed" in stale.content["detail"]
    wrong_match = invoke(workspace, "edit_file", path="candidate/src/theory.md", expected_sha256=sha(original),
        edits=[{"old_text": "absent text", "new_text": "a desired conclusion"}])
    assert wrong_match.is_error
    assert (tmp_path / "candidate/src/theory.md").read_text() == original
    changed = invoke(workspace, "edit_file", path="candidate/src/theory.md", expected_sha256=sha(original),
        edits=[{"old_text": "unresolved", "new_text": "revised"}])
    assert changed.state_changed
    assert (tmp_path / "candidate/src/theory.md").read_text() == original.replace("unresolved", "revised")
    removed = invoke(workspace, "remove_file", path="candidate/src/theory.md", expected_sha256=changed.content["sha256"])
    assert removed.state_changed and not (tmp_path / "candidate/src/theory.md").exists()


def test_readonly_source_and_host_evidence_are_not_writable(workspace, tmp_path):
    for name in ("sources/brief.md", "candidate/metrics.json", "candidate/correct.json"):
        assert invoke(workspace, "write_file", path=name, expected_sha256=None, content="forged").is_error
    assert (tmp_path / "public/brief.md").read_text().startswith("Opaque brief.")
    assert not (tmp_path / "candidate/metrics.json").exists()


def test_atomic_source_replacement_preserves_executable_permissions(workspace, tmp_path):
    path = tmp_path / "candidate/src/helper.sh"
    path.parent.mkdir(parents=True)
    content = "#!/bin/sh\nprintf 'opaque'\n"
    path.write_text(content)
    path.chmod(0o755)
    result = invoke(workspace, "write_file", path="candidate/src/helper.sh", content=content, expected_sha256=sha(content))
    assert not result.state_changed and not result.is_error
    assert path.stat().st_mode & 0o777 == 0o755
    edited = invoke(workspace, "edit_file", path="candidate/src/helper.sh", expected_sha256=sha(content),
        edits=[{"old_text": "opaque", "new_text": "revised"}])
    assert edited.state_changed and path.stat().st_mode & 0o777 == 0o755
    assert next(row for row in workspace.files() if row["path"].endswith("helper.sh"))["mode"] == 0o755


def test_symlinks_and_hardlinks_do_not_expand_grants(workspace, tmp_path):
    (tmp_path / "public/link.txt").symlink_to(tmp_path / "private.txt")
    os.link(tmp_path / "private.txt", tmp_path / "public/hard.txt")
    (tmp_path / "candidate/src").mkdir(parents=True)
    (tmp_path / "candidate/src/escape").symlink_to(tmp_path, target_is_directory=True)
    for name in ("sources/link.txt", "sources/hard.txt"):
        assert invoke(workspace, "read_file", path=name).is_error
    assert invoke(workspace, "write_file", path="candidate/src/escape/new.txt", content="x", expected_sha256=None).is_error
    assert not (tmp_path / "new.txt").exists()
    assert {row["path"] for row in workspace.files()} == {"sources/brief.md"}


@pytest.mark.parametrize("linked_parent", ["resources", ".local-api", "program_1"])
def test_native_stage_rejects_linked_grant_ancestors(tmp_path, linked_parent):
    (tmp_path / "program_0/src").mkdir(parents=True)
    (tmp_path / "program_0/program_spec.toml").write_text('schema_version=1\ncode_root="src"\n')
    private = tmp_path / "private"
    (private / "search").mkdir(parents=True)
    (private / "search/evaluate.py").write_text("private evaluator fixture")
    (tmp_path / linked_parent).symlink_to(private, target_is_directory=True)
    with pytest.raises(ValueError, match="ancestors"):
        stage_workspace(tmp_path, tmp_path)


class FixtureBackend:
    provider_name = "local"

    def __init__(self, actions):
        self.actions = iter(actions)
        self.requests = []

    def generate_client_tool_turn(self, request):
        self.requests.append(request)
        name, inputs = next(self.actions)
        call_id = str(len(self.requests))
        return ClientToolTurnResponse(
            content_blocks=({"type": "tool_use", "id": call_id, "name": name, "input": inputs},),
            tool_calls=(ClientToolCall(call_id=call_id, name=name, input=inputs),),
            text="", provider="local", model=request.model,
            metadata={"provider_usage": {"input_tokens": 10, "output_tokens": 5}})


def run(workspace, backend, destination, *, max_turns=6):
    return run_file_session(backend=backend, workspace=workspace, prompt="Opaque research-stage brief.",
        model="frozen-fixture-model", max_tokens=8192, temperature=1.0, max_turns=max_turns,
        session_dir=destination, session_id="opaque-attempt", deployment_identity={"revision": "exact-fixture"})


@pytest.fixture
def posthoc_root(tmp_path):
    root = tmp_path / "analysis"
    (root / "task_bundle/evidence").mkdir(parents=True)
    (root / "task_bundle/program_0/src").mkdir(parents=True)
    (root / "task_bundle/resources/search/statistical-research").mkdir(parents=True)
    (root / "task_bundle/resources/search/statistical-research/SKILL.md").write_text("Retained statistical reporting guidance.")
    (root / "analysis_spec.json").write_text(json.dumps({"expected_outputs": ["notes/limitations.md"]}))
    (root / "rubric_contract.json").write_text("{}")
    (root / "task_bundle/task.md").write_text("Interpret the supplied opaque outcomes; do not repeat execution.")
    (root / "task_bundle/evidence/arbitrary-table.csv").write_text("condition,value\na,17\nb,23\n")
    (root / "task_bundle/program_0/src/theory.md").write_text("An unassessed argument.")
    (root / "task_bundle/program_0/scientific_review.md").write_text("Public source-review findings; a gap remains.")
    (root / "task_bundle/program_0/evaluate.py").write_text("private evaluator")
    (root / "task_bundle/program_0/scientific_review_session.json").write_text("private review context")
    return root


def test_posthoc_reads_only_public_inputs_and_writes_declared_reports(posthoc_root):
    workspace = posthoc_workspace(posthoc_root)
    table = "task_bundle/evidence/arbitrary-table.csv"
    assert invoke(workspace, "read_file", path=table).content["content"] == "condition,value\na,17\nb,23\n"
    guidance = "task_bundle/resources/search/statistical-research/SKILL.md"
    assert "Retained statistical" in invoke(workspace, "read_file", path=guidance).content["content"]
    review = "task_bundle/program_0/scientific_review.md"
    assert "gap remains" in invoke(workspace, "read_file", path=review).content["content"]
    for path in (table, guidance, review, "task_bundle/program_0/src/theory.md", "analysis_spec.json"):
        assert invoke(workspace, "write_file", path=path, content="changed", expected_sha256=None).is_error
    for path in ("task_bundle/program_0/evaluate.py", "task_bundle/program_0/scientific_review_session.json"):
        assert invoke(workspace, "read_file", path=path).is_error
    for path in ("analysis_summary.md", "interestingness_rubric.json", "analysis_manifest.json", "rubric_status.json", "notes/limitations.md"):
        assert not invoke(workspace, "write_file", path=path, content="model-authored", expected_sha256=None).is_error
    assert invoke(workspace, "write_file", path="undeclared.md", content="x", expected_sha256=None).is_error


@pytest.mark.parametrize("output", ["task_bundle/forged.csv", ".local-api/session/result.json", "reports/*", "../escape.md", "/tmp/escape.md", "analysis_spec.json", ""])
def test_posthoc_output_declaration_cannot_expand_authority(posthoc_root, output):
    (posthoc_root / "analysis_spec.json").write_text(json.dumps({"expected_outputs": [output]}))
    with pytest.raises((ValueError, ClientToolInputError)):
        posthoc_workspace(posthoc_root)


def test_posthoc_retained_session_interprets_actual_table_without_execution(posthoc_root, tmp_path):
    workspace = posthoc_workspace(posthoc_root)
    before = {row["path"]: row["sha256"] for row in workspace.files()}
    report = "# Observed results\nThe supplied table contains 17 and 23. No additional computation or proof was performed.\n"
    backend = FixtureBackend([
        ("read_file", {"path": "task_bundle/evidence/arbitrary-table.csv"}),
        ("write_file", {"path": "analysis_summary.md", "content": report, "expected_sha256": None}),
        ("finish", {"disposition": "candidate", "summary": "Interpretation ready for review."}),
    ])
    result = run(workspace, backend, tmp_path / "posthoc-session")
    observation = backend.requests[1].messages[-1]["content"][0]
    assert "a,17" in observation["content"] and "b,23" in observation["content"]
    assert (posthoc_root / "analysis_summary.md").read_text() == report
    after = {row["path"]: row["sha256"] for row in workspace.files()}
    assert all(after[path] == digest for path, digest in before.items())
    assert all("run" not in tool.name and "execute" not in tool.name for tool in backend.requests[0].tools)
    assert result.terminal_payload["scientific_acceptance"] is False


def test_same_model_receives_raw_failure_and_owns_revision(workspace, tmp_path):
    backend = FixtureBackend([
        ("read_file", {"path": "private.txt"}),
        ("write_file", {"path": "candidate/src/theory.tex", "content": "% Model-authored unresolved argument\n", "expected_sha256": None}),
        ("finish", {"disposition": "candidate", "summary": "Ready for independent assessment, not proven."}),
    ])
    result = run(workspace, backend, tmp_path / "session")
    feedback = backend.requests[1].messages[-1]["content"][0]
    assert feedback["is_error"] and "outside the stage's file grants" in feedback["content"]
    assert (tmp_path / "candidate/src/theory.tex").read_text() == "% Model-authored unresolved argument\n"
    assert result.terminal_payload["scientific_acceptance"] is False
    assert result.model == "frozen-fixture-model" and result.turns == 3
    saved = json.loads((tmp_path / "session/result.json").read_text())
    assert saved["provider_usage"] == {"input_tokens": 30, "output_tokens": 15}
    assert any(row["path"] == "candidate/src/theory.tex" for row in saved["final_files"])
    assert all("run" not in tool.name and "execute" not in tool.name for tool in backend.requests[0].tools)
    with pytest.raises(FileExistsError):
        run(workspace, backend, tmp_path / "session")


def test_honest_gap_is_terminal_but_not_scientific_success(workspace, tmp_path):
    result = run(workspace, FixtureBackend([("finish", {"disposition": "gap", "summary": "Unresolved assumption."})]), tmp_path / "gap")
    assert result.terminal_payload == {"disposition": "gap", "summary": "Unresolved assumption.", "scientific_acceptance": False}


def test_exhaustion_preserves_session_without_fallback(workspace, tmp_path):
    backend = FixtureBackend([("write_file", {"path": "candidate/src/theory.md", "content": "Unfinished argument", "expected_sha256": None})])
    with pytest.raises(ClientToolLoopError):
        run(workspace, backend, tmp_path / "incomplete", max_turns=1)
    record = json.loads((tmp_path / "incomplete/result.json").read_text())
    assert record["status"] == "INCOMPLETE" and record["provider_usage"]["output_tokens"] == 5
    assert len(backend.requests) == 1
    assert {row["path"]: row["sha256"] for row in record["final_files"]}["candidate/src/theory.md"] == sha("Unfinished argument")
    identity = json.loads((tmp_path / "incomplete/input.json").read_text())["identity"]
    assert record["durable_state_identity"] == stable_hash({"authorization_fingerprint": stable_hash(identity), "files": record["final_files"]})
    assert record["session_ref"]["durable_state_identity"] == record["durable_state_identity"]
    assert record["durable_state_identity"] != stable_hash(identity)


@pytest.mark.skipif(os.name != "posix", reason="Native upstream runner uses POSIX process signals")
@pytest.mark.parametrize("termination", [signal.SIGTERM, signal.SIGKILL])
def test_native_cli_interruption_preserves_completed_response_and_source(tmp_path, termination):
    (tmp_path / "program_0/src").mkdir(parents=True)
    (tmp_path / "program_0/program_spec.toml").write_text('schema_version=1\ncode_root="src"\n')
    (tmp_path / "prompt.md").write_text("Opaque source authoring fixture.")
    receipt = tmp_path / "deployment.json"
    receipt.write_text("fixture")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"model": "fixture", "base_url": "http://127.0.0.1:8081/v1",
        "max_tokens": 8192, "temperature": 1.0, "timeout_seconds": 30, "max_turns": 5,
        "deployment_ref": {"path": str(receipt), "sha256": sha("fixture")}}))
    marker = tmp_path / "waiting"

    def child():
        import scripts.run_agentic_api as cli

        class BlockingBackend(FixtureBackend):
            def generate_client_tool_turn(self, request):
                if self.requests:
                    marker.touch()
                    time.sleep(30)
                return super().generate_client_tool_turn(request)

        cli.LocalChatGeneratorBackend = lambda **kwargs: BlockingBackend([
            ("write_file", {"path": "program_1/src/theory.md", "content": "Unassessed argument", "expected_sha256": None})])
        os.chdir(tmp_path)
        os.environ.update(AI_STATISTICIAN_API_CONFIG=str(config), TASK_SOURCE_DIR=str(tmp_path), ATTEMPT_ID="interrupted")
        sys.argv = ["run_agentic_api", "--prompt-file", "prompt.md", "--model", "fixture"]
        cli.main()

    process = multiprocessing.get_context("fork").Process(target=child)
    process.start()
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and process.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.exists()
        os.kill(process.pid, termination)
        process.join(timeout=5)
        assert not process.is_alive() and process.exitcode != 0
    finally:
        if process.is_alive():
            process.kill()
            process.join(timeout=5)
    record = json.loads((tmp_path / ".local-api/session/result.json").read_text())
    assert record["status"] == ("INTERRUPTED" if termination == signal.SIGTERM else "INCOMPLETE")
    assert record["provider_usage"] == {"input_tokens": 10, "output_tokens": 5}
    assert record["phase"] == "model_in_flight"
    assert record["messages"][-1]["content"][0]["type"] == "tool_result"
    assert record["resume_supported"] is False
    assert {r["path"]: r["sha256"] for r in record["final_files"]}["program_1/src/theory.md"] == sha("Unassessed argument")


def test_native_stage_excludes_evaluator_and_only_grants_current_source(tmp_path):
    (tmp_path / "program_0/src").mkdir(parents=True)
    (tmp_path / "program_0/program_spec.toml").write_text('schema_version = 1\ncode_root = "src"\n')
    (tmp_path / "evaluate.py").write_text("private evaluator fixture")
    (tmp_path / "task.md").write_text("public task")
    stage = stage_workspace(tmp_path, tmp_path / "task-source")
    assert invoke(stage, "read_file", path="evaluate.py").is_error
    assert invoke(stage, "read_file", path="task.md").content["content"] == "public task"
    assert invoke(stage, "write_file", path="program_1/src/algorithm.R", content="# Model authored R\n", expected_sha256=None).state_changed


def test_idea_receives_prior_source_feedback_without_evaluator_access(tmp_path):
    source, results = tmp_path / "task", tmp_path / "results"
    (source / "program_0/src").mkdir(parents=True)
    (source / "program_0/program_spec.toml").write_text('schema_version=1\ncode_root="src"\n')
    (source / "task.md").write_text("Opaque task")
    (source / "target_rubrics.json").write_text("[]")
    prior = results / "ideas/01_prior"
    (prior / "program_1/src").mkdir(parents=True)
    (prior / "program_1/src/program.py").write_text("# prior author source")
    (prior / "program_1/harness_evaluate_stderr.log").write_text("opaque raw execution failure")
    diagnostic = prior / "program_1/public/observations.json"
    diagnostic.parent.mkdir()
    diagnostic.write_text('{"stderr":"opaque failure in structured result"}')
    (prior / "program_1/private.json").write_text("private evaluator observations")
    receipt = prior / "program_1/evaluation_manifest.json"
    receipt.write_text(json.dumps({
        "public_outputs": [{"path": "public/observations.json", "kind": "derived"},
                           {"path": "public/not-produced.json", "kind": "derived"}],
        "evidence_records": {"public/observations.json": sha(diagnostic.read_text()),
                             "private.json": sha("private evaluator observations")},
    }))
    (prior / "evaluate.py").write_text("private evaluator")
    (results / "attempts_history.jsonl").write_text('{"attempt_status":"fail"}\n')
    idea = stage_workspace(results / "_idea_generation/next", source, stage="idea", results=results)
    assert "the host owns global memory bookkeeping" in idea.instructions
    assert "operator's fixed acceptance contract" in idea.instructions
    assert "Upstream workflow instructions apply only where compatible" in idea.instructions
    assert invoke(idea, "read_file", path="history/ideas/01_prior/program_1/harness_evaluate_stderr.log").content["content"] == "opaque raw execution failure"
    assert invoke(idea, "read_file", path="history/ideas/01_prior/program_1/public/observations.json").content["content"] == diagnostic.read_text()
    assert invoke(idea, "read_file", path="history/ideas/01_prior/program_1/private.json").is_error
    assert invoke(idea, "read_file", path="history/ideas/01_prior/program_1/public/not-produced.json").is_error
    assert invoke(idea, "write_file", path="history/ideas/01_prior/program_1/public/observations.json", content="changed", expected_sha256=sha(diagnostic.read_text())).is_error
    assert invoke(idea, "read_file", path="history/ideas/01_prior/evaluate.py").is_error
    assert invoke(idea, "write_file", path="task_requirements.json", content="weaker", expected_sha256=sha("[]")).is_error
    assert invoke(idea, "write_file", path="idea_bundle.json", content="{}", expected_sha256=None).state_changed
    assert invoke(idea, "write_file", path="memory.md", content="unscoped notes", expected_sha256=None).is_error
    (source / "program_0/src/aliased").symlink_to(prior, target_is_directory=True)
    assert invoke(idea, "read_file", path="program_0/src/aliased/evaluate.py").is_error
    diagnostic.write_text("changed after receipt")
    with pytest.raises(ValueError, match="differs from its receipt"):
        stage_workspace(results / "_idea_generation/another", source, stage="idea", results=results)


def test_api_config_binds_deployment_and_cannot_switch_model(tmp_path):
    receipt = tmp_path / "deployment.json"
    receipt.write_text('{"revision":"opaque"}')
    config = {"model": "pinned", "base_url": "http://127.0.0.1:8081/v1", "max_tokens": 16384,
        "temperature": 1.0, "max_turns": 128, "timeout_seconds": 1800,
        "deployment_ref": {"path": str(receipt), "sha256": sha(receipt.read_text())}}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    loaded, identity = load_config(path, model="pinned")
    assert loaded == config and identity["config"] == config
    with pytest.raises(ValueError, match="no substitution"):
        load_config(path, model="other")
    receipt.write_text("changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_config(path, model="pinned")
