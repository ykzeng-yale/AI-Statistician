from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from ai_statistician.agent_runtime import AgentTask
from ai_statistician.architect_coordinator_llm import (
    _architect_metric_authoring_deferred_for_active_replan,
    _architect_runtime_evaluation_contract,
    _required_architect_plan_subsystems,
)
from ai_statistician.architect_metric_contract_authoring import (
    _fresh_candidate_requirement_set_errors,
    _metric_candidate_repair_available,
)
from ai_statistician.cli import (
    _apply_research_agent_runtime_evaluation_model_policy,
    _apply_research_agent_runtime_research_eval_profile,
    build_parser,
)
from ai_statistician.fingerprint import stable_hash
from ai_statistician.generated_code_semantic_reviewer_llm import (
    GeneratedCodeSemanticReviewerConfig,
    LLMGeneratedCodeSemanticReviewerAgent,
)
from ai_statistician.model_backend import (
    LIVE_EVALUATION_CLAUDE_MODEL_TIER,
    StaticJSONGeneratorBackend,
)
from ai_statistician.research_agent_runtime import (
    ResearchAgentRuntimeConfig,
    _architect_candidate_seed,
    _coding_agent_packet_validation_state,
    _post_empirical_evidence_task,
    _runtime_retire_resolved_generated_code_semantic_review_replan,
    _runtime_requested_evidence_contract,
    _runtime_simulation_metric_protocol_guard,
    run_research_agent_runtime,
)
from ai_statistician.research_architect import (
    LLMTheoryDeveloperAgent,
    ResearchArchitectConfig,
    THEORY_PROMPT_MODE_SERIOUS_CAPABILITY,
    _theory_developer_prompt_mode,
)
from ai_statistician.research_evaluation import (
    build_research_evaluation_summary,
)
from ai_statistician.research_schema import OpenResearchQuestion


def test_research_eval_contract_requires_research_lane_without_formalizer() -> None:
    research = _architect_runtime_evaluation_contract(
        {"evaluation_mode": "research_eval", "n_runs": 100}
    )
    strict = _architect_runtime_evaluation_contract(
        {"evaluation_mode": "capability_eval", "n_runs": 100}
    )

    assert research["capability_eval_requires_generated_algorithm_code"] is True
    assert research["capability_eval_requires_generated_simulation_code"] is True
    assert research["capability_eval_requires_generated_code_semantic_review"] is True
    assert research["capability_eval_requires_typed_metric_contracts"] is True
    assert research["research_evaluation_requires_generated_algorithm_code"] is True
    assert research["research_evaluation_requires_generated_simulation_code"] is True
    assert research[
        "research_evaluation_requires_generated_code_semantic_review"
    ] is True
    assert research["research_evaluation_requires_typed_metric_contracts"] is True
    assert research["capability_eval_requires_formalizer_lean_candidate"] is False
    assert strict["capability_eval_requires_formalizer_lean_candidate"] is True

    required = set(_required_architect_plan_subsystems(research))
    assert {
        "RetrievalMemory",
        "TheoryDeveloper",
        "AlgorithmEngineer",
        "SimulationEvaluator",
        "GeneratedCodeSemanticReviewer",
        "CriticEvaluator",
    } <= required
    assert "FormalizationEvaluator" not in required
    assert "ProofEngineer" not in required


def test_mixed_metric_findings_keep_bounded_candidate_repair_available() -> None:
    assert _metric_candidate_repair_available(
        [
            {"repair_scope": "upstream_theory"},
            {"repair_scope": "metric_contract"},
        ]
    ) is True
    assert _metric_candidate_repair_available(
        [{"repair_scope": "upstream_theory"}]
    ) is False


def test_fresh_accepted_artifact_retires_only_its_exact_stale_replan() -> None:
    stale_replan = {
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm:rejected",
        "review_execution_id": "review-execution:rejected",
        "repair_scope": "source_code",
    }
    context = {
        "runtime_generated_code_semantic_review_replan": stale_replan,
        "environment_feedback": {
            "feedback_type": "generated_code_semantic_review_feedback",
            "source_manifest_id": "algorithm:rejected",
            "semantic_review_execution_id": "review-execution:rejected",
        },
        "runtime_feedback_loop": {
            "semantic_review_execution_id": "review-execution:rejected"
        },
    }
    accepted_review = {
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm:fresh",
        "source_manifest_hash": "fresh-hash",
        "execution_id": "review-execution:accepted",
        "review_packet_id": "review-packet:accepted",
        "overall_verdict": "ACCEPT",
    }

    resolved = _runtime_retire_resolved_generated_code_semantic_review_replan(
        architect_context=context,
        accepted_review=accepted_review,
    )

    assert "runtime_generated_code_semantic_review_replan" not in resolved
    assert "environment_feedback" not in resolved
    assert "runtime_feedback_loop" not in resolved
    resolution = resolved[
        "runtime_generated_code_semantic_review_replan_resolution"
    ]
    assert resolution["rejected_source_manifest_id"] == "algorithm:rejected"
    assert resolution["accepted_source_manifest_id"] == "algorithm:fresh"

    defensive_context = {
        "runtime_generated_code_semantic_review_replan": stale_replan,
        "runtime_generated_code_semantic_review_replan_resolution": resolution,
    }
    assert _architect_metric_authoring_deferred_for_active_replan(
        defensive_context
    ) is False
    assert _architect_metric_authoring_deferred_for_active_replan(context) is True

    unrelated_acceptance = {
        **accepted_review,
        "source_subsystem": "SimulationEvaluator",
    }
    unchanged = _runtime_retire_resolved_generated_code_semantic_review_replan(
        architect_context=context,
        accepted_review=unrelated_acceptance,
    )
    assert unchanged["runtime_generated_code_semantic_review_replan"] == (
        stale_replan
    )


def test_research_eval_routes_accepted_empirical_artifacts_to_critic() -> None:
    question = OpenResearchQuestion(
        id="generic_research_eval",
        title="Generic research evaluation",
        description="Develop and evaluate a new statistical procedure.",
    )
    context = {
        "runtime_requested_evidence_contract": {
            "evaluation_mode": "research_eval"
        }
    }
    task = _post_empirical_evidence_task(
        question=question,
        packet_id="theory:1",
        simulation_manifest_id="simulation:1",
        algorithm_sandbox_manifest_id="algorithm:1",
        architect_context=context,
    )

    assert task.owner_subsystem == "CriticEvaluator"
    assert task.inputs["theory_packet_id"] == "theory:1"
    assert task.inputs["simulation_manifest_id"] == "simulation:1"
    assert task.inputs["algorithm_sandbox_manifest_id"] == "algorithm:1"

    debug_task = _post_empirical_evidence_task(
        question=question,
        packet_id="theory:1",
        simulation_manifest_id="simulation:1",
        algorithm_sandbox_manifest_id="algorithm:1",
        architect_context={},
    )
    assert debug_task.owner_subsystem == "FormalizationEvaluator"


def test_research_eval_keeps_serious_theory_and_independent_review_gate(
    tmp_path,
) -> None:
    contract = _runtime_requested_evidence_contract(
        formal_verification_policy="advisory",
        recommended_research_path="simulation_first",
        evaluation_mode="research_eval",
    )
    assert contract["capability_eval_requires_generated_algorithm_code"] is True
    assert contract["capability_eval_requires_generated_simulation_code"] is True
    assert contract["capability_eval_requires_generated_code_semantic_review"] is True
    assert contract["research_evaluation_requires_generated_algorithm_code"] is True
    assert contract["research_evaluation_requires_generated_simulation_code"] is True
    assert contract[
        "research_evaluation_requires_generated_code_semantic_review"
    ] is True
    assert contract["research_evaluation_requires_typed_metric_contracts"] is True
    assert contract["capability_eval_requires_formalizer_lean_candidate"] is False
    assert (
        _theory_developer_prompt_mode(
            {
                "architect_runtime_plan": {
                    "evidence_contract": {"evaluation_mode": "research_eval"}
                }
            }
        )
        == THEORY_PROMPT_MODE_SERIOUS_CAPABILITY
    )

    with pytest.raises(ValueError, match="GeneratedCodeSemanticReviewer"):
        run_research_agent_runtime(
            [],
            tmp_path,
            theory_developer=None,
            config=ResearchAgentRuntimeConfig(evaluation_mode="research_eval"),
        )


def test_research_eval_returns_before_formal_postprocessing(tmp_path) -> None:
    theory_developer = LLMTheoryDeveloperAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=ResearchArchitectConfig(
            provider_name="static",
            model="static",
            model_tier="sonnet",
            serious_model="static",
            serious_model_tier="sonnet",
        ),
    )
    semantic_reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model="static",
            model_tier="sonnet",
        ),
    )

    manifest = run_research_agent_runtime(
        [],
        tmp_path,
        theory_developer=theory_developer,
        generated_code_semantic_reviewer=semantic_reviewer,
        config=ResearchAgentRuntimeConfig(evaluation_mode="research_eval"),
    )

    assert manifest["research_eval_typed_endpoint_reached"] is True
    assert manifest["post_runtime_formal_workflow_executed"] is False
    assert manifest["post_runtime_formal_workflow_skip_reason"] == (
        "research_eval_typed_endpoint"
    )
    assert "formalization" not in manifest["runtime_stage"]
    assert "runtime_theorem_reduction_closure_work_orders_jsonl" not in (
        manifest["artifacts"]
    )


def test_research_eval_exports_pending_continuations_for_every_question(
    tmp_path,
) -> None:
    theory_developer = LLMTheoryDeveloperAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=ResearchArchitectConfig(
            provider_name="static",
            model="static",
            model_tier="sonnet",
            serious_model="static",
            serious_model_tier="sonnet",
        ),
    )
    semantic_reviewer = LLMGeneratedCodeSemanticReviewerAgent(
        provider=StaticJSONGeneratorBackend({}),
        config=GeneratedCodeSemanticReviewerConfig(
            provider_name="static",
            model="static",
            model_tier="sonnet",
        ),
    )
    questions = [
        OpenResearchQuestion("pending_q1", "Pending one", "", ()),
        OpenResearchQuestion("pending_q2", "Pending two", "", ()),
    ]
    initial_tasks = {
        question.id: AgentTask(
            task_id=f"simulation:{question.id}",
            owner_subsystem="SimulationEvaluator",
            objective="Exercise question-bound continuation export.",
            inputs={
                "question": {
                    "id": question.id,
                    "title": question.title,
                    "description": question.description,
                    "tags": list(question.tags),
                },
                "theory_packet_id": "",
                "architect_context": {},
            },
        )
        for question in questions
    }

    manifest = run_research_agent_runtime(
        questions,
        tmp_path,
        theory_developer=theory_developer,
        generated_code_semantic_reviewer=semantic_reviewer,
        initial_task_overrides=initial_tasks,
        config=ResearchAgentRuntimeConfig(
            evaluation_mode="research_eval",
            max_iterations=1,
        ),
    )

    assert manifest["n_incomplete_pending_next_tasks"] == 2
    assert set(manifest["incomplete_pending_next_task_by_question"]) == {
        "pending_q1",
        "pending_q2",
    }
    pending_rows = [
        json.loads(line)
        for line in Path(
            manifest["artifacts"]["runtime_pending_next_tasks_jsonl"]
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert [row["question_id"] for row in pending_rows] == [
        "pending_q1",
        "pending_q2",
    ]
    assert all(
        row["pending_next_task"]["owner_subsystem"] == "TheoryDeveloper"
        for row in pending_rows
    )
    legacy_pending = json.loads(
        Path(
            manifest["artifacts"]["runtime_pending_next_task_json"]
        ).read_text(encoding="utf-8")
    )
    assert legacy_pending == pending_rows[0]


def test_research_eval_profile_enables_live_research_agents_only() -> None:
    args = argparse.Namespace(
        research_eval=True,
        capability_eval=False,
        capability_eval_preset="none",
        provider="anthropic",
        architect_coordinator_provider="same",
        simulation_engineer_provider="same",
        algorithm_engineer_provider="same",
        critic_evaluator_provider="same",
        generated_code_semantic_reviewer_provider="none",
        formalizer_provider="same",
        formal_target_semantic_reviewer_provider="same",
        formal_target_semantic_review_required=True,
        formal_verification_policy="required",
        recommended_research_path="proof_first",
        architect_metric_repair_ownership_router=False,
        architect_max_tokens=5000,
        serious_theory_model_tier="sonnet",
        serious_theory_max_tokens=1000,
        llm_timeout_seconds=120.0,
    )

    _apply_research_agent_runtime_research_eval_profile(args)
    _apply_research_agent_runtime_evaluation_model_policy(args)

    assert args.generated_code_semantic_reviewer_provider == "same"
    assert args.formalizer_provider == "none"
    assert args.formal_target_semantic_reviewer_provider == "none"
    assert args.formal_target_semantic_review_required is False
    assert args.formal_verification_policy == "advisory"
    assert args.recommended_research_path == "simulation_first"
    assert args.architect_metric_repair_ownership_router is True
    assert args.architect_max_tokens == 8000
    assert args.architect_metric_semantic_reviewer_max_tokens == 12000
    assert args.serious_theory_model_tier == "haiku"
    assert args.evaluation_claude_model_tier == "haiku"
    assert args.evaluation_claude_model == "claude-haiku-4-5-20251001"
    assert args.serious_theory_max_tokens >= 10000
    assert args.llm_timeout_seconds == 240.0
    assert args.max_iterations == 24
    assert args.architect_metric_protocol_max_fresh_candidate_revisions == 1
    assert args.coding_agent_packet_validation_max_lineage_failures == 4

    parsed = build_parser().parse_args(
        ["research-agent-runtime", "--research-eval"]
    )
    assert parsed.research_eval is True
    assert parsed.capability_eval is False
    assert parsed.architect_metric_protocol_max_upstream_theory_revisions == 1
    assert parsed.generated_code_semantic_review_max_upstream_theory_revisions == 1
    assert parsed.architect_metric_protocol_max_fresh_candidate_revisions == 0
    with pytest.raises(SystemExit):
        build_parser().parse_args(
            [
                "research-agent-runtime",
                "--research-eval",
                "--capability-eval",
            ]
        )


def test_fresh_candidate_seed_override_is_explicit_and_bounded() -> None:
    assert _architect_candidate_seed(
        architect_context={"runtime_candidate_seed": 8128},
        default_seed=41,
    ) == 8128
    assert _architect_candidate_seed(
        architect_context={"runtime_candidate_seed": -1},
        default_seed=41,
    ) == 41


def test_fresh_candidate_must_change_the_rejected_requirement_set() -> None:
    context = {"source_requirement_set_id": "requirements:rejected"}
    assert _fresh_candidate_requirement_set_errors(
        candidate_requirement_set_id="requirements:rejected",
        fresh_candidate_revision_context=context,
    )
    assert _fresh_candidate_requirement_set_errors(
        candidate_requirement_set_id="requirements:fresh",
        fresh_candidate_revision_context=context,
    ) == []


def test_packet_validation_budget_survives_theory_revision_and_stays_source_owned() -> None:
    base_inputs = {
        "question": {"id": "generic_packet_budget"},
        "theory_packet_id": "theory:stable",
        "architect_context": {},
    }
    first_task = AgentTask(
        task_id="algorithm:first",
        owner_subsystem="AlgorithmEngineer",
        objective="validate generated packet",
        inputs=base_inputs,
    )
    first = _coding_agent_packet_validation_state(
        task=first_task,
        feedback_type="algorithm_engineer_packet_validation_feedback",
        validation_label="AlgorithmEngineer packet",
        validation_errors=["missing required implementation binding"],
        replan_after_attempts=2,
        max_lineage_failures=3,
    )
    assert first["lineage_packet_validation_round"] == 1
    assert first["packet_validation_replan_required"] is False
    assert first["packet_validation_source_retry_escalated"] is False

    replanned_context = {
        "runtime_packet_validation_attempt_ledger": first[
            "packet_validation_attempt_ledger"
        ]
    }
    second_task = AgentTask(
        task_id="algorithm:after-architect",
        owner_subsystem="AlgorithmEngineer",
        objective="retry after Architect replan",
        inputs={
            **base_inputs,
            "theory_packet_id": "theory:revised",
            "architect_context": replanned_context,
        },
    )
    second = _coding_agent_packet_validation_state(
        task=second_task,
        feedback_type="algorithm_engineer_packet_validation_feedback",
        validation_label="AlgorithmEngineer packet",
        validation_errors=["missing required implementation binding"],
        replan_after_attempts=2,
        max_lineage_failures=3,
    )
    assert second["lineage_packet_validation_round"] == 2
    assert second["packet_validation_lineage_key"] == first[
        "packet_validation_lineage_key"
    ]
    assert second["packet_validation_replan_required"] is False
    assert second["packet_validation_source_retry_escalated"] is True
    assert second["packet_validation_repair_owner"] == "AlgorithmEngineer"
    assert second["packet_validation_repair_owner_basis"] == (
        "local_packet_validator"
    )

    third_task = AgentTask(
        task_id="algorithm:after-second-architect",
        owner_subsystem="AlgorithmEngineer",
        objective="bounded final retry",
        inputs={
            **base_inputs,
            "theory_packet_id": "theory:revised-again",
            "architect_context": {
                "runtime_packet_validation_attempt_ledger": second[
                    "packet_validation_attempt_ledger"
                ]
            },
        },
    )
    third = _coding_agent_packet_validation_state(
        task=third_task,
        feedback_type="algorithm_engineer_packet_validation_feedback",
        validation_label="AlgorithmEngineer packet",
        validation_errors=["missing required implementation binding"],
        replan_after_attempts=2,
        max_lineage_failures=3,
    )
    assert third["lineage_packet_validation_round"] == 3
    assert third["packet_validation_lineage_budget_exhausted"] is True
    assert third["packet_validation_replan_required"] is False
    assert third["packet_validation_source_retry_escalated"] is False
    lineage_row = third["packet_validation_attempt_ledger"][
        third["packet_validation_lineage_key"]
    ]
    assert lineage_row["observed_theory_packet_ids"] == [
        "theory:stable",
        "theory:revised",
        "theory:revised-again",
    ]


def test_simulation_guard_blocks_before_proposal_or_execution() -> None:
    question = OpenResearchQuestion(
        id="generic_simulation_guard",
        title="Guard confirmatory execution",
        description="Require a reviewed theory-bound metric protocol.",
    )
    task = AgentTask(
        task_id="simulation:guard",
        owner_subsystem="SimulationEvaluator",
        objective="run confirmatory simulation",
        inputs={
            "question": {
                "id": question.id,
                "title": question.title,
                "description": question.description,
                "tags": [],
            },
            "theory_packet_id": "theory:guard",
        },
    )
    context = {
        "architect_runtime_plan": {
            "evidence_contract": {
                "capability_eval_requires_typed_metric_contracts": True,
                "empirical_metric_requirements": [],
                "metric_protocol_execution_authorized": False,
            }
        }
    }

    result = _runtime_simulation_metric_protocol_guard(
        task=task,
        question=question,
        theory_packet_id="theory:guard",
        theory_packet={"packet_id": "theory:guard"},
        architect_context=context,
        exploratory_diagnostic=False,
    )

    assert result is not None
    assert result.status == "REROUTE"
    assert result.next_task is not None
    assert result.next_task.owner_subsystem == "ArchitectCoordinator"
    block = next(iter(result.produced_artifacts.values()))
    assert block["execution_attempted"] is False
    assert block["execution_authorized"] is False


def test_research_evaluation_summary_requires_every_research_artifact() -> None:
    question = {"id": "generic_research_eval"}
    artifacts = {
        "theory": {
            "artifact_kind": "TheoryDerivationPacket",
            "packet_id": "theory",
            "question": question,
            "serious_theory_mode": True,
            "provider": "anthropic",
        },
        "architect": {
            "artifact_kind": "ArchitectCoordinatorProposalPacket",
            "packet_id": "architect",
            "evidence_contract": {
                "empirical_metric_protocol_phase": "preexecution_review_accepted",
                "metric_protocol_execution_authorized": True,
                "empirical_metric_requirement_set_id": "metric-set:1",
                "empirical_metric_requirements": [{"requirement_id": "metric:1"}],
                "empirical_metric_requirements_preexecution_review": {
                    "overall_verdict": "ACCEPT",
                    "independent_agent": True,
                    "independent_invocation": True,
                    "independent_model": True,
                    "independent_model_tier": True,
                },
            },
        },
        "algorithm": {
            "artifact_kind": "RuntimeAlgorithmSandboxManifest",
            "manifest_id": "algorithm",
            "theory_packet_id": "theory",
            "n_live_generated_code_executed": 1,
            "n_passed": 1,
            "n_live_generated_code_execution_failed": 0,
        },
        "simulation": {
            "artifact_kind": "RuntimeSimulationManifest",
            "manifest_id": "simulation",
            "theory_packet_id": "theory",
            "runtime_architect_control": {
                "architect_coordinator_proposal_id": "architect"
            },
            "n_live_generated_simulation_sandbox_executed": 1,
            "generated_simulation_passed": True,
            "simulation_passed": True,
            "n_generated_simulation_typed_metric_contracts_declared": 1,
            "n_generated_simulation_typed_metric_contracts_evaluated": 1,
            "n_generated_simulation_typed_metric_contracts_passed": 1,
            "n_generated_simulation_typed_metric_contracts_failed": 0,
            "generated_simulation_sandbox_prototypes": [
                {
                    "smoke_passed": True,
                    "metric_requirement_set_id": "metric-set:1",
                    "metric_requirement_authority_validated": True,
                    "metric_contract_evaluation": {
                        "metric_requirement_set_id": "metric-set:1",
                        "metric_requirement_authority_validated": True,
                        "n_contracts": 1,
                        "n_passed": 1,
                        "n_failed": 0,
                        "all_required_passed": True,
                    },
                }
            ],
        },
        "critic": {
            "artifact_kind": "RuntimeCriticEvaluatorManifest",
            "manifest_id": "critic",
            "question": question,
            "theory_packet_id": "theory",
            "algorithm_sandbox_manifest_id": "algorithm",
            "simulation_manifest_id": "simulation",
            "evidence_contract_decision": {"runtime_status": "ACCEPTED"},
        },
    }
    accepted_review = {
        "artifact_kind": "RuntimeGeneratedCodeSemanticReviewExecutionManifest",
        "semantic_review_accepted": True,
        "independent_agent": True,
        "independent_invocation": True,
        "independent_model": True,
        "reviewer_model_tier": LIVE_EVALUATION_CLAUDE_MODEL_TIER,
        "confirmatory_empirical_evidence_eligible": True,
    }
    artifacts["algorithm_review"] = {
        **accepted_review,
        "source_subsystem": "AlgorithmEngineer",
        "source_manifest_id": "algorithm",
        "source_manifest_hash": stable_hash(artifacts["algorithm"]),
    }
    artifacts["simulation_review"] = {
        **accepted_review,
        "source_subsystem": "SimulationEvaluator",
        "source_manifest_id": "simulation",
        "source_manifest_hash": stable_hash(artifacts["simulation"]),
    }
    result = {
        "status": "ACCEPTED",
        "blackboard": {"artifacts": artifacts},
        "traces": (
            {
                "subsystem": "CriticEvaluator",
                "status": "ACCEPTED",
                "produced_artifact_ids": ("critic",),
            },
        ),
    }

    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is True

    artifacts["stale_algorithm"] = {
        **artifacts["algorithm"],
        "manifest_id": "stale_algorithm",
    }
    artifacts["algorithm"]["n_passed"] = 0
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is False
    assert summary["all_questions_mode_conformant"] is True
    assert summary["all_questions_research_eval_complete"] is False

    artifacts["algorithm"]["n_passed"] = 1
    artifacts["algorithm_review"]["source_manifest_hash"] = stable_hash(
        artifacts["algorithm"]
    )
    result["traces"] = (
        *result["traces"],
        {"subsystem": "FormalizationEvaluator"},
    )
    summary = build_research_evaluation_summary(
        [result], evaluation_mode="research_eval", schema_version="test"
    )
    assert summary["all_questions_research_loop_complete"] is True
    assert summary["all_questions_mode_conformant"] is False
    assert summary["all_questions_research_eval_complete"] is False
    assert summary["rows"][0]["mode_conformance"][
        "strict_formal_lane_not_executed"
    ] is False
