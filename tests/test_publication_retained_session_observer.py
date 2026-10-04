"""Observer qualification with no inference, deployment or scientific authority."""
import csv
from dataclasses import replace
from io import StringIO
import json
from pathlib import Path

import pytest

from ai_statistician.client_tool_loop import ClientToolExecutionContext, ClientToolInputError
from ai_statistician.model_backend import ClientToolCall
from benchmarks.publication_deployment_qualification_20261003 import observe_retained_session as observer


def test_planned_assets_and_fixture_are_bound_without_reading_weights():
    plan = json.loads(Path("benchmarks/publication_deployment_qualification_20261003/retained_session_plan.json").read_text())
    assert observer.digest(Path(plan["asset_plan"])) == plan["asset_plan_sha256"]
    rows = observer.fixture_records(plan)
    assert len(rows) == 192 and len({row["event_id"] for row in rows}) == 192
    assert rows[0]["status"] == "pending" and rows[1]["status"] == "recorded"
    assert len(rows[0]["receipt"]) == 16 and rows[0]["note"].split() == ["note"] * 256
    assert plan["request"]["tool_choice"] == "auto"


def test_file_feedback_returns_to_same_executor_and_preserves_source_content(tmp_path):
    plan = {"check_id": "opaque-reader-fixture", "pages": 2, "records_per_page": 2,
            "inert_note_words_per_record": 3}
    rows = observer.fixture_records(plan)
    tools, execute = observer.tools_and_executor(plan, tmp_path, rows)
    context = ClientToolExecutionContext(0, 0, 1, 0)
    page = execute(ClientToolCall("page", "read_page", {"page": 1}), context)
    assert page.content["records"] == rows[2:]
    assert not page.terminal and not page.is_error
    with pytest.raises(ClientToolInputError, match="page outside"):
        execute(ClientToolCall("bad", "read_page", {"page": 2}), context)
    write = ClientToolCall("write", "write_file", {"path": "ledger.csv", "content": "wrong-header\n", "append": False})
    execute(write, context)
    failed = execute(ClientToolCall("finish", "finish", {}), context)
    assert failed.is_error and not failed.terminal
    assert (tmp_path / "ledger.csv").read_text() == "wrong-header\n"
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["event_id", "receipt", "status"])
    writer.writeheader()
    writer.writerows({key: row[key] for key in writer.fieldnames} for row in reversed(rows))
    execute(replace(write, input={**write.input, "content": buffer.getvalue()}), context)
    execute(ClientToolCall("report", "write_file", {"path": "report.md", "content": "# Unresolved fixture\n", "append": False}), context)
    complete = execute(ClientToolCall("finish", "finish", {}), context)
    assert complete.terminal and not complete.is_error
    assert complete.terminal_payload == {"file_validation": "passed"}
    assert {tool.name for tool in tools} == {"read_page", "read_file", "write_file", "finish", "read_workspace_history"}
    assert observer.check_files(tmp_path, rows) == []
    (tmp_path / "ledger.csv").write_text(buffer.getvalue() + buffer.getvalue().splitlines(keepends=True)[1])
    assert "duplicate event_id" in observer.check_files(tmp_path, rows)
