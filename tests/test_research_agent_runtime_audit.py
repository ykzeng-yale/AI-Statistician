from ai_statistician.research_agent_runtime_audit import _scorecard


def _row(scorecard: dict[str, object], requirement_id: str) -> dict[str, object]:
    return next(
        row
        for row in scorecard["rows"]  # type: ignore[index]
        if row["requirement_id"] == requirement_id
    )


def test_code_revision_ownership_cannot_pass_without_executed_sources() -> None:
    traces = [
        {"question_id": "task-one", "status": "BLOCKED"},
        {"question_id": "task-two", "status": "BLOCKED"},
    ]
    scorecard = _scorecard(
        {
            "config": {"evaluation_mode": "capability_eval"},
            "llm_topology_policy_ok": True,
            "llm_runtime_topology": {"llm_agents": []},
        },
        traces,
        [],
        [],
        {
            "manifest_readable": True,
            "canonical_runtime_endpoint": True,
            "integrated_evidence_only": True,
            "legacy_post_runtime_fallback_absent": True,
            "runtime_streams_readable": True,
        },
    )

    ownership = _row(scorecard, "source_producer_owns_code_revision")
    assert ownership["passed"] is False
    assert "algorithm_executed=[]" in str(ownership["evidence"])
    assert "simulation_executed=[]" in str(ownership["evidence"])
