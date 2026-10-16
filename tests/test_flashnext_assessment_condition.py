"""Opaque experiment plumbing, not assessment of a statistical argument."""

import json

import pytest

from benchmarks.publication_assessment_flashnext_20261016.qualify import run_cases
from test_agentic_api_workspace import FixtureBackend


@pytest.mark.parametrize("outcome", ["PASS", "FAIL", "ERROR"])
def test_assessment_keeps_contexts_separate_and_stops_only_on_execution_error(tmp_path, outcome):
    bank = tmp_path / "bank"
    bank.mkdir()
    for name in ("task.md", "reference.md", "a.md", "b.md"):
        (bank / name).write_text("Opaque source; no expected scientific answer.")
    (bank / "private-key.md").write_text("Private fixture key, never model input.")
    (bank / "bank.json").write_text(json.dumps({"question_file": "task.md", "reference_files": ["reference.md"],
        "rubric": {"claims": [{"claim_id": "opaque", "obligation": "Assess only the opaque fixture."}]}}))
    plan = {"bank_root": str(bank), "scope": "Opaque mechanism fixture, not science.",
            "cases": [{"id": f"case-{i}", "files": [name], "expected_status": "PASS"}
                      for i, name in enumerate(("a.md", "b.md"))]}
    actions = []
    for i in range(1 if outcome == "ERROR" else 2):
        actions.extend([
            ("read_file", {"path": "candidate/document-0.md"}),
            ("read_file", {"path": "private-key.md"}),
            ("write_file", {"path": "review.md", "content": "Opaque review " + str(i), "expected_sha256": None}),
        ])
        if outcome != "ERROR":
            actions.append(("submit_review", {"verdicts": [{"id": "opaque", "status": outcome}]}))
    backend = FixtureBackend(actions)
    output = tmp_path / "result"
    kwargs = dict(plan=plan, backend=backend, config={"model": "opaque-fixed-model", "max_tokens": 8192,
        "temperature": 1, "max_turns": 8}, identity={"revision": "opaque-fixed"},
        prompt="Inspect task.md and the candidate/source files.", output=output)
    result = run_cases(**kwargs)
    assert result["scientific_qualification"] == "NOT_ESTABLISHED"
    assert "Private fixture key" not in str(backend.requests)
    if outcome == "PASS":
        assert result["status"] == "LABELS_MATCHED_ARGUMENT_EXAMINATION_REQUIRED"
        assert len(backend.requests[4].messages) == 1
        assert all(row["labels_match"] for row in result["cases"])
    elif outcome == "ERROR":
        assert result["cases"][1]["state"] == "NOT_RUN"
        assert result["cases"][0]["state"] == "ERROR"
    else:
        assert result["status"] == "LABEL_MISMATCH"
        assert all(row["state"] == "COMPLETED" and not row["labels_match"] for row in result["cases"])
    with pytest.raises(FileExistsError):
        run_cases(**kwargs)


@pytest.mark.parametrize("statuses,expected", [
    (["PASS", "PASS"], "PASS"), (["PASS", "UNCERTAIN"], "UNCERTAIN"), (["UNCERTAIN", "FAIL"], "FAIL"),
])
def test_native_overall_disposition_does_not_erase_partial_or_failed_obligations(tmp_path, statuses, expected):
    for name in ("task.md", "reference.md", "candidate.md"):
        (tmp_path / name).write_text("Opaque source fixture.")
    ids = ("first", "second")
    (tmp_path / "bank.json").write_text(json.dumps({"question_file": "task.md", "reference_files": ["reference.md"],
        "rubric": {"claims": [{"claim_id": name, "obligation": "Opaque obligation."} for name in ids]}}))
    backend = FixtureBackend([
        ("write_file", {"path": "review.md", "content": "Opaque report, not mathematical evidence.", "expected_sha256": None}),
        ("submit_review", {"verdicts": [{"id": name, "status": status} for name, status in zip(ids, statuses)]}),
    ])
    result = run_cases(plan={"scope": "Fixture", "bank_root": str(tmp_path), "cases": [{
        "id": "case-0", "files": ["candidate.md"], "expected_status": expected}]}, backend=backend,
        config={"model": "opaque-fixed-model", "max_tokens": 8192, "temperature": 1, "max_turns": 4},
        identity={}, prompt="Inspect only the supplied files.", output=tmp_path / "output")
    assert result["cases"][0]["status"] == expected
    assert result["scientific_qualification"] == "NOT_ESTABLISHED"


def test_an_empty_panel_cannot_pass_without_a_model_call(tmp_path):
    backend = FixtureBackend([])
    with pytest.raises(ValueError, match="nonempty control panel"):
        run_cases(plan={"cases": []}, backend=backend, config={}, identity={}, prompt="", output=tmp_path / "output")
    assert not backend.requests and not (tmp_path / "output").exists()
