from pathlib import Path

from statlean_agent.agents import get_agent
from statlean_agent.worktrees import WorktreeManager


def test_dry_run_assignment() -> None:
    manager = WorktreeManager(Path("/tmp/repo"))
    assignment = manager.create(get_agent("formalization"), dry_run=True)
    assert assignment.agent_key == "formalization"
    assert assignment.branch == "agent/formalization"
    assert assignment.dry_run

