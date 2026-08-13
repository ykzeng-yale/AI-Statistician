from ai_statistician.research_agent_runtime_audit import (
    _failed_simulation,
    _has_direct_revision,
    _scorecard,
    _source_owner_revision_summary,
)


def _row(scorecard: dict[str, object], requirement_id: str) -> dict[str, object]:
    return next(
        row
        for row in scorecard["rows"]  # type: ignore[index]
        if row["requirement_id"] == requirement_id
    )


def test_code_revision_ownership_cannot_pass_without_executed_sources() -> None:
    assert _source_owner_revision_summary([], []) == (True, 0, 0, 0, set())
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


def test_code_revision_ownership_uses_hash_bound_workspace_lineage() -> None:
    question_id = "task-one"
    revision_workspace = {
        "artifact_id": f"{question_id}:estimator",
        "workspace_operation": "targeted_revision",
        "parent_code_draft_hash": "parent-draft-hash",
        "submitted_code_draft_hash": "child-draft-hash",
        "initial_check_result_hash": "initial-check-hash",
        "terminal_check_result_hash": "terminal-check-hash",
        "initial_check_accepted": False,
        "source_changed": True,
        "source_updates": 1,
        "sandbox_checks": 1,
        "runtime_executed_tool_calls": 2,
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "model_owned_source": True,
        "runtime_edited_source": False,
        "accepted": True,
        "transcript_fingerprint": "workspace-transcript-hash",
        "source_revision_lineage": {
            "parent_manifest_id": "simulation:unrelated",
            "feedback_supplied_to_generator": True,
            "lineage_contract_complete": True,
        },
    }
    evidence = [
        {
            "question_id": question_id,
            "artifact_id": "simulation:failed",
            "evidence_type": "simulation",
            "payload": {
                "n_generated_simulation_sandbox_executed": 1,
                "n_generated_simulation_sandbox_passed": 0,
                "n_generated_simulation_sandbox_metric_gate_failed": 1,
                "scientific_code_workspaces": [],
            },
        },
        {
            "question_id": question_id,
            "artifact_id": "algorithm:revised",
            "evidence_type": "algorithm_sandbox",
            "payload": {
                "scientific_code_workspaces": [revision_workspace],
            },
        },
    ]
    unrelated = _has_direct_revision(
        evidence,
        failure_type="simulation",
        proposal_type="llm_simulation_engineer_proposal",
        failed=_failed_simulation,
    )
    assert unrelated == (False, 1, 0)

    revision_workspace["source_revision_lineage"]["parent_manifest_id"] = (
        "simulation:failed"
    )
    bound = _has_direct_revision(
        evidence,
        failure_type="simulation",
        proposal_type="llm_simulation_engineer_proposal",
        failed=_failed_simulation,
    )
    assert bound == (True, 1, 1)


def test_source_owner_revision_audit_uses_explicit_backedge_and_replay() -> None:
    question_id = "task-one"
    task_id = "algorithm-consumer-observation:task-one:abc"
    workspace = {
        "artifact_id": "task-one:estimator",
        "workspace_operation": "targeted_revision",
        "parent_code_draft_hash": "parent-source",
        "submitted_code_draft_hash": "child-source",
        "initial_check_result_hash": "initial-check",
        "terminal_check_result_hash": "terminal-check",
        "initial_check_accepted": False,
        "source_changed": True,
        "source_updates": 1,
        "sandbox_checks": 1,
        "runtime_executed_tool_calls": 1,
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "model_owned_source": True,
        "runtime_edited_source": False,
        "accepted": True,
        "transcript_fingerprint": "transcript",
    }
    evidence = [
        {
            "question_id": question_id,
            "task_id": task_id,
            "evidence_type": "algorithm_sandbox",
            "payload": {"scientific_code_workspaces": [workspace]},
        },
        {
            "question_id": question_id,
            "task_id": "simulation:statistical-failure",
            "evidence_type": "simulation",
            "artifact_id": "simulation:failed-metric",
            "payload": {
                "n_generated_simulation_sandbox_executed": 1,
                "n_generated_simulation_sandbox_passed": 0,
                "n_generated_simulation_sandbox_metric_gate_failed": 1,
            },
        },
    ]
    observations = [
        {
            "question_id": question_id,
            "task_id": task_id,
            "observation_type": "algorithm_consumer_source_workspace_resumed",
            "payload": {
                "source_manifest_id": "algorithm:parent",
                "source_revision_artifact_ids": ["estimator"],
            },
        },
        {
            "question_id": question_id,
            "task_id": "simulation:restored",
            "observation_type": "scientific_consumer_continuation_restored",
            "payload": {"consumer_resume_manifest_id": "simulation:parent"},
        },
    ]

    assert _source_owner_revision_summary(evidence, observations) == (
        True,
        1,
        1,
        1,
        {question_id},
    )


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
