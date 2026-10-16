"""Opaque reviewer transport fixtures, not mathematical accuracy tests."""

import hashlib
import json

import pytest

from ai_statistician.agentic_scientific_review import ScientificReviewWorkspace, run_scientific_review
from ai_statistician.agentic_api_workspace import FileGrant
from test_agentic_api_workspace import FixtureBackend, invoke, run, sha


@pytest.fixture
def review_input(tmp_path):
    task = tmp_path / "attempt"
    program = task / "program_1"
    (program / "src").mkdir(parents=True)
    (program / "src/theory.md").write_text("# Opaque candidate argument\nAn unresolved fixture step.\n")
    (program / "src/program.py").write_text("print('opaque')\n")
    records = {"src/" + path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (program / "src").iterdir()}
    (program / "evaluation_manifest.json").write_text(json.dumps({"source_records": records}))
    (program / "metrics.json").write_text('{"hidden_outcome":"do not inspect"}')
    (task / "task.md").write_text("Opaque source review fixture, no scientific claim.")
    rubrics = task / "active_rubrics.json"
    rubrics.write_text(json.dumps([{"id": "argument", "type": "review", "description": "Opaque criterion."}]))
    (task / "resources/search").mkdir(parents=True)
    (task / "resources/search/source.md").write_text("Permitted reference fixture.")
    return dict(program=program, task=task, rubrics_file=rubrics, sources=task,
        config={"model": "frozen-fixture-model", "temperature": 1.0, "max_tokens": 8192, "max_turns": 8},
        deployment_identity={"revision": "exact-fixture"}, prompt="Read the exact candidate and report uncertainty honestly.")


@pytest.mark.parametrize("status", ["PASS", "FAIL", "UNCERTAIN"])
def test_review_is_separate_readonly_and_hash_bound(review_input, status):
    report = f"# Opaque review\nFixture disposition {status}; not mathematical evidence.\n"
    backend = FixtureBackend([
        ("read_file", {"path": "candidate/src/theory.md"}),
        ("read_file", {"path": "candidate/metrics.json"}),
        ("write_file", {"path": "candidate/src/theory.md", "content": "replacement", "expected_sha256": None}),
        ("write_file", {"path": "review.md", "content": report, "expected_sha256": None}),
        ("submit_review", {"verdicts": [{"id": "argument", "status": status}]}),
    ])
    before = (review_input["program"] / "src/theory.md").read_bytes()
    receipt = run_scientific_review(backend=backend, **review_input)
    assert receipt["verdicts"] == [{"id": "argument", "status": status}]
    assert receipt["report"]["sha256"] == sha(report)
    assert receipt["model"] == "frozen-fixture-model"
    assert "not proof" in receipt["scope"]
    assert (review_input["program"] / "src/theory.md").read_bytes() == before
    assert len(backend.requests[0].messages) == 1
    assert all(tool.name != "finish" for tool in backend.requests[0].tools)
    feedback = backend.requests[2].messages[-1]["content"][0]
    assert feedback["is_error"] and "outside" in feedback["content"]
    assert "do not inspect" not in str(backend.requests)
    session = json.loads((review_input["program"] / receipt["session"]["path"]).read_text())
    assert session["provider_usage"] == {"input_tokens": 50, "output_tokens": 25}
    assert receipt["session"]["sha256"] == hashlib.sha256(
        (review_input["program"] / receipt["session"]["path"]).read_bytes()).hexdigest()
    with pytest.raises(FileExistsError, match="consumed"):
        run_scientific_review(backend=FixtureBackend([]), **review_input)


def test_review_cannot_start_on_changed_evaluated_source(review_input):
    (review_input["program"] / "src/theory.md").write_text("Changed after evaluation")
    backend = FixtureBackend([])
    with pytest.raises(ValueError, match="evaluated source"):
        run_scientific_review(backend=backend, **review_input)
    assert not backend.requests


@pytest.mark.parametrize("name", ["program_0", "program_01", "program_x", "program_-1"])
def test_review_requires_canonical_candidate_identity(review_input, name):
    backend = FixtureBackend([])
    review_input["program"] = review_input["task"] / name
    with pytest.raises(ValueError, match="candidate"):
        run_scientific_review(backend=backend, **review_input)
    assert not backend.requests


def test_review_submission_does_not_infer_report_or_missing_judgments(tmp_path):
    source = tmp_path / "theory.md"
    source.write_text("Opaque source")
    workspace = ScientificReviewWorkspace((FileGrant("candidate/theory.md", source),
        FileGrant("review.md", tmp_path / "review.md", writable=True)), ("first", "second"))
    assert invoke(workspace, "submit_review", verdicts=[{"id": "first", "status": "PASS"}]).is_error
    complete = [{"id": name, "status": "UNCERTAIN"} for name in ("first", "second")]
    assert invoke(workspace, "submit_review", verdicts=complete).is_error
    assert invoke(workspace, "write_file", path="review.md", content="Explicit fixture gap", expected_sha256=None).state_changed
    assert invoke(workspace, "submit_review", verdicts=[complete[0], complete[0]]).is_error
    assert invoke(workspace, "submit_review", verdicts=complete).terminal
    source.write_text("Changed source")
    assert invoke(workspace, "submit_review", verdicts=complete).is_error


def test_reviewer_keeps_transport_errors_in_its_own_context(tmp_path):
    source = tmp_path / "theory.md"
    source.write_text("Opaque source")
    workspace = ScientificReviewWorkspace((FileGrant("candidate/theory.md", source),
        FileGrant("review.md", tmp_path / "review.md", writable=True)), ("argument",))
    backend = FixtureBackend([
        ("submit_review", {"verdicts": []}),
        ("read_file", {"path": "candidate/theory.md"}),
        ("write_file", {"path": "review.md", "content": "Unresolved fixture issue.", "expected_sha256": None}),
        ("submit_review", {"verdicts": [{"id": "argument", "status": "UNCERTAIN"}]}),
    ])
    result = run(workspace, backend, tmp_path / "session")
    assert result.terminal_payload["verdicts"][0]["status"] == "UNCERTAIN"
    assert backend.requests[1].messages[-1]["content"][0]["is_error"]
    assert "source review" in result.terminal_payload["scope"]
