from pathlib import Path


def test_public_docs_name_route_planning_brief_artifacts_and_claude_tiers() -> None:
    text = Path("docs/library_aware_formalization_gap_planner.md").read_text(
        encoding="utf-8"
    )

    assert (
        "formalization_gap_planner_llm_route_planner_route_planning_briefs.jsonl"
        in text
    )
    assert (
        "formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json"
        in text
    )
    assert (
        "contract/formalization_gap_planner_llm_route_planner_route_planning_brief.schema.json"
        in text
    )
    assert "claude-haiku-4-5-20251001" in text
    assert "claude-sonnet-4-6" in text
    assert "claude-opus-4-8" in text
    assert "codex_exec" in text
    assert "not theorem proof evidence" in text
