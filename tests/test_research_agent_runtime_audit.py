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


def test_direct_formalizer_workspace_supplies_rag_source_and_revision_evidence() -> None:
    question_id = "task-one"
    evidence = [
        {
            "question_id": question_id,
            "evidence_type": "retrieval_memory",
            "payload": {"formal_source_hits": 2},
        },
        {
            "question_id": question_id,
            "evidence_type": "formalizer_lean_candidate_client_tool_loop",
            "payload": {
                "candidate_source_hash": "source-hash",
                "source_changed": True,
                "source_updates": 2,
                "local_lean_checks": 2,
                "n_formal_rag_tool_calls": 3,
                "latest_check_compiled": False,
                "provider": "anthropic",
                "model": "claude-haiku-4-5-20251001",
                "model_owned_lean_code": True,
                "runtime_selected_lean_code": False,
            },
        },
    ]
    scorecard = _scorecard(
        {
            "config": {"evaluation_mode": "capability_eval"},
            "llm_topology_policy_ok": True,
            "llm_runtime_topology": {"llm_agents": []},
        },
        [{"question_id": question_id, "status": "BLOCKED"}],
        [],
        evidence,
        {
            "manifest_readable": True,
            "canonical_runtime_endpoint": True,
            "integrated_evidence_only": True,
            "legacy_post_runtime_fallback_absent": True,
            "runtime_streams_readable": True,
        },
    )

    assert _row(scorecard, "task_bound_formal_rag_observed")["passed"] is True
    assert _row(scorecard, "llm_generated_lean_source_observed")["passed"] is True
    assert _row(
        scorecard,
        "same_formalizer_revised_from_raw_lean_feedback",
    )["passed"] is True


def _theory_evidence(*, with_workspace: bool) -> dict[str, object]:
    payload: dict[str, object] = {
        "theory_derivation_contract": {
            "n_derivation_steps": 5,
            "n_equation_chain_steps": 4,
            "n_assumption_ledger_rows": 3,
        }
    }
    if with_workspace:
        payload["llm_client_tool_loop"] = {
            "artifact_kind": "TheoryDeveloperWorkspaceEvidence",
            "workspace_operation": "initial_discovery",
            "accepted": True,
            "model_owned_theory": True,
            "runtime_edited_theory": False,
            "reads": 1,
            "submissions": 1,
            "changed_artifact_names": ["problem_card"],
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
        }
    return {
        "question_id": "task-one",
        "evidence_type": "llm_theory_derivation",
        "payload": payload,
    }


def test_rigorous_theory_requires_model_owned_initial_workspace() -> None:
    common = {
        "config": {"evaluation_mode": "capability_eval"},
        "llm_topology_policy_ok": True,
        "llm_runtime_topology": {"llm_agents": []},
    }
    integrity = {
        "manifest_readable": True,
        "canonical_runtime_endpoint": True,
        "integrated_evidence_only": True,
        "legacy_post_runtime_fallback_absent": True,
        "runtime_streams_readable": True,
    }
    traces = [{"question_id": "task-one", "status": "BLOCKED"}]

    without_workspace = _scorecard(
        common,
        traces,
        [],
        [_theory_evidence(with_workspace=False)],
        integrity,
    )
    with_workspace = _scorecard(
        common,
        traces,
        [],
        [_theory_evidence(with_workspace=True)],
        integrity,
    )

    rejected = _row(
        without_workspace,
        "rigorous_theory_derivation_observed",
    )
    accepted = _row(
        with_workspace,
        "rigorous_theory_derivation_observed",
    )
    assert rejected["passed"] is False
    assert "content=['task-one']" in str(rejected["evidence"])
    assert "model_owned_initial_workspace=[]" in str(
        rejected["evidence"]
    )
    assert accepted["passed"] is True
