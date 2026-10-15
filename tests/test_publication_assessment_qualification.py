from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys

import pytest

from benchmarks.publication_assessment_qualification_20261015 import qualify


def _fixture(tmp_path, monkeypatch):
    def save(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value) if not isinstance(value, str) else value)
        return path

    model = "Qwen3-4B-Instruct-2507"
    settings = {"model": model, "model_path": "opaque-weights", "model_ids": [model],
                "context": 131072, "slots": 1, "template_sha256": hashlib.sha256(b"template").hexdigest(),
                "seed": 20261015, "temperature": 0, "top_k": 20, "top_p": 0.8, "min_p": 0}
    bank = save("bank.json", {"task_id": "opaque", "question_file": "setup.md", "reference_files": ["reference.md"],
        "rubric": {"claims": [{"claim_id": "obligation"}]},
        "calibration": [{"case_id": "opaque-control", "files": ["control.md"], "expected_status": "FAIL"}],
        "candidate_mode_negative": [{"case_id": "opaque-negative", "files": ["control.md"], "expected_status": "FAIL"}],
        "candidate_files": ["candidate.md"], "private_answer_key": "key.md"})
    sources = [save(name, content) for name, content in (
        ("setup.md", "opaque-question"), ("reference.md", "opaque-reference"),
        ("control.md", "opaque-control"), ("candidate.md", "opaque-candidate"), ("key.md", "HIDDEN-KEY"))]
    binary = save("binary", "opaque-binary")
    assets = save("assets.json", {"download": {"verified_path": str(binary)},
        "weights_sha256": qualify.digest(binary), "server_binary": str(binary),
        "server_sha256": qualify.digest(binary), "library_directory": str(tmp_path), "library_sha256": {}})
    plan = save("plan.json", {"output": str(tmp_path / "output"), "scope": "mechanism-only",
        "bank": str(bank), "asset_plan": str(assets), "active_settings": settings,
        "inputs": [{"path": str(path), "sha256": qualify.digest(path)} for path in [bank, assets, *sources]],
        "server_url": "http://127.0.0.1:8081", "request_timeout_seconds": 7200,
        "max_tokens": 16384, "limitations": "opaque-fixture-not-scientific-authority"})
    props = {"model_alias": model, "model_path": "opaque-weights", "total_slots": 1, "chat_template": "template",
        "default_generation_settings": {"n_ctx": 131072, "params": {key: settings[key] for key in
            ("seed", "temperature", "top_k", "top_p", "min_p")}}}
    observations = [props, {"data": [{"id": model}]}]

    class Opener:
        def open(self, *_args, **_kwargs):
            return io.BytesIO(json.dumps(observations.pop(0)).encode())

    class Backend:
        def __init__(self, *_args, **_kwargs):
            self.attempts = 0

    monkeypatch.setattr(qualify.urllib.request, "build_opener", lambda *_: Opener())
    monkeypatch.setattr(qualify.subprocess, "check_output", lambda *_args, **_kwargs: "opaque-observation")
    monkeypatch.setattr(qualify, "RecordingBackend", Backend)
    monkeypatch.setattr(sys, "argv", ["qualify", "--plan", str(plan)])
    return plan, sources, observations


def test_assessment_assembly_reuses_frozen_review_without_key_or_source_edits(tmp_path, monkeypatch):
    plan, sources, _ = _fixture(tmp_path, monkeypatch)

    def review(**kwargs):
        assert kwargs["model"] == "Qwen3-4B-Instruct-2507" and kwargs["model_tier"] == "local"
        assert kwargs["max_tokens"] == 16384 and kwargs["candidate_adjudication_strategy"] == "integrated_single"
        assert kwargs["visible_question"]["question"] == "opaque-question"
        assert kwargs["reference_documents"][0]["content"] == "opaque-reference"
        assert kwargs["candidate_documents"][0]["content"] == "opaque-candidate"
        assert kwargs["calibration_cases"][0]["documents"][0]["content"] == "opaque-control"
        assert "HIDDEN-KEY" not in str(kwargs)
        return {"semantic_judge_calibrated": True, "candidate_status": "PASS"}

    monkeypatch.setattr(qualify, "run_theory_semantic_gold_judge", review)
    before = {path: path.read_bytes() for path in sources}
    assert qualify.main() == 0
    result = json.loads((tmp_path / "output/result.json").read_text())
    assert result["scientific_qualification"] == "not_established"
    assert result["inputs_unchanged"] is True and result["model_attempts"] == 0
    assert {path: path.read_bytes() for path in sources} == before
    with pytest.raises(FileExistsError):
        qualify.main()


@pytest.mark.parametrize("defect", ["input_changed", "input_missing", "active_settings", "review_stopped"])
def test_assessment_precheck_or_review_failure_is_not_retried(tmp_path, monkeypatch, defect):
    plan, sources, observations = _fixture(tmp_path, monkeypatch)
    calls = []

    def review(**kwargs):
        calls.append(kwargs)
        raise ValueError("opaque-unfinished-review")

    monkeypatch.setattr(qualify, "run_theory_semantic_gold_judge", review)
    if defect == "input_changed":
        sources[0].write_text("changed-question")
    elif defect == "input_missing":
        sources[0].unlink()
    elif defect == "active_settings":
        observations[0]["total_slots"] = 2
    assert qualify.main() == 1
    assert len(calls) == int(defect == "review_stopped")
    result = json.loads((tmp_path / "output/result.json").read_text())
    assert result["scientific_qualification"] == "not_established" and result["status"] == "stopped"
    assert not (tmp_path / "output/judgment.json").exists()
