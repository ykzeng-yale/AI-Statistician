from __future__ import annotations

import json

from ai_statistician.formalizer_llm import build_formalizer_prompt
from ai_statistician.agent_runtime import AgentTask
from ai_statistician.research_agent_runtime import (
    _formalizer_lean_candidate_revision_feedback,
    _formalizer_proof_state_routing_manifest,
    _formalizer_proof_state_routing_task,
)
from ai_statistician.research_schema import (
    FormalSubclaim,
    OpenResearchQuestion,
)


QUESTION = OpenResearchQuestion(
    id="generic_formal_feedback",
    title="Generic formal feedback",
    description="Regenerate an exact Lean source from environment observations.",
    tags=("formalization",),
)


def test_formalizer_receives_complete_source_and_raw_tool_observations() -> None:
    source = "theorem exact_target : True := by\n" + "  skip\n" * 900
    stdout = "compiler stdout\n" + "x" * 6000 + "STDOUT_TAIL"
    stderr = "compiler stderr\n" + "y" * 6000 + "STDERR_TAIL"
    manifest = {
        "artifact_kind": "RuntimeFormalizerLeanCandidateMaterialization",
        "manifest_id": "materialization:complete-feedback",
        "future_manifest_observation": {"opaque": [1, 2, 3]},
        "n_candidate_sources": 1,
        "n_candidate_artifacts_written": 1,
        "n_precheck_rejected": 0,
        "n_local_lean_checked": 1,
        "n_local_lean_compiled": 0,
        "candidate_rows": [
            {
                "candidate_id": "exact-target",
                "candidate_kind": "formal_target_lean_statement_sketch",
                "source_field": "formal_targets",
                "lean_source": source,
                "local_lean_attempted": True,
                "local_lean_compiled": False,
                "local_lean_exit_status": "1",
                "local_lean_stdout": stdout,
                "local_lean_stderr": stderr,
                "future_compiler_observation": {
                    "provider_specific": "PRESERVE_ME"
                },
                "future_repair_diagnostics": {
                    "raw_provider_message": "PRESERVE_DESPITE_LEGACY_SUFFIX"
                },
                "preferred_tool_order": ["runtime-authored-legacy-recipe"],
            }
        ],
    }
    reviewer_feedback = {
        "feedback_type": "formal_target_semantic_review_feedback",
        "findings": [
            {
                "finding_id": "reviewer:finding",
                "required_change": "MODEL_REVIEWER_OBSERVATION_MUST_SURVIVE",
            }
        ],
    }

    feedback = _formalizer_lean_candidate_revision_feedback(
        manifest,
        prior_environment_feedback=reviewer_feedback,
    )

    assert feedback is not None
    assert feedback["future_manifest_observation"] == {"opaque": [1, 2, 3]}
    row = feedback["candidate_diagnostics"][0]
    assert row["lean_source"] == source
    assert row["local_lean_stdout"] == stdout
    assert row["local_lean_stderr"] == stderr
    assert row["future_compiler_observation"]["provider_specific"] == (
        "PRESERVE_ME"
    )
    assert row["future_repair_diagnostics"]["raw_provider_message"] == (
        "PRESERVE_DESPITE_LEGACY_SUFFIX"
    )

    prompt = build_formalizer_prompt(
        question=QUESTION,
        theory_packet={"packet_id": "theory:complete-feedback"},
        simulation_manifest={},
        algorithm_manifest={},
        registered_problem={},
        theorem_goals=[],
        proof_bank_obligation_catalog=[],
        proof_bank_runtime_memory_summary={},
        environment_feedback=feedback,
    )
    payload = json.loads(prompt[prompt.index('{"question":') :])
    carried = payload["runtime_environment_feedback"]
    carried_row = carried["candidate_diagnostics"][0]
    assert carried_row["lean_source"] == source
    assert carried_row["local_lean_stdout"].endswith("STDOUT_TAIL")
    assert carried_row["local_lean_stderr"].endswith("STDERR_TAIL")
    assert carried_row["future_compiler_observation"]["provider_specific"] == (
        "PRESERVE_ME"
    )
    assert carried_row["future_repair_diagnostics"]["raw_provider_message"] == (
        "PRESERVE_DESPITE_LEGACY_SUFFIX"
    )
    assert carried_row["preferred_tool_order"] == [
        "runtime-authored-legacy-recipe"
    ]
    assert carried["prior_environment_feedback"]["findings"][0][
        "required_change"
    ] == "MODEL_REVIEWER_OBSERVATION_MUST_SURVIVE"


def test_proof_state_feedback_is_complete_and_budget_exhaustion_routes_architect() -> None:
    long_diagnostic = "diagnostic:" + "d" * 6000 + "DIAGNOSTIC_TAIL"
    long_goal = "goal:" + "g" * 6000 + "GOAL_TAIL"
    subclaim = FormalSubclaim(
        id="subclaim:exact-target",
        title="Exact target",
        status="FORMAL_GAP",
        claim="The exact target remains open.",
        claim_type="lean_obligation",
        proof_obligation_id="exact-target",
        lean_statement="theorem exact_target : True := by sorry",
        kernel_verified=False,
    )
    proposal = {
        "packet_id": "formalizer:complete-proof-state",
        "future_proposal_field": {"opaque": "PROPOSAL_FIELD"},
    }
    materialization = {
        "manifest_id": "materialization:complete-proof-state",
        "candidate_rows": [
            {
                "candidate_id": "exact-target",
                "lean_source": "theorem exact_target : True := by\n  exact True.intro",
                "future_materialization_field": "MATERIALIZATION_FIELD",
            }
        ],
    }
    row = {
        "feedback_id": "proof-state:exact-target",
        "subclaim_id": subclaim.id,
        "attempt_status": "local_lean_failed",
        "diagnostics": [long_diagnostic, *[f"diagnostic-{i}" for i in range(8)]],
        "residual_goals": [long_goal, *[f"goal-{i}" for i in range(8)]],
        "route_revision_recommended": True,
        "subclaim_kernel_verified": False,
        "future_proof_state_field": {"opaque": "PROOF_STATE_FIELD"},
    }

    manifest = _formalizer_proof_state_routing_manifest(
        question=QUESTION,
        task_id="formalize:complete-proof-state",
        source_subsystem="FormalizationEvaluator",
        environment_feedback={},
        max_revision_rounds=0,
        proofengineer_available=True,
        formalization_manifest_id="formalization:complete-proof-state",
        proof_state_feedback_manifest_id="proof-state-manifest:complete",
        proposal_packet=proposal,
        subclaims=[subclaim],
        proof_state_rows=[row],
        lean_candidate_materialization=materialization,
    )

    assert manifest is not None
    feedback = manifest["environment_feedback"]
    carried_row = feedback["proof_state_feedback_rows"][0]
    assert len(carried_row["diagnostics"]) == 9
    assert carried_row["diagnostics"][0].endswith("DIAGNOSTIC_TAIL")
    assert carried_row["residual_goals"][0].endswith("GOAL_TAIL")
    assert carried_row["future_proof_state_field"]["opaque"] == (
        "PROOF_STATE_FIELD"
    )
    assert feedback["source_formalizer_proposal"] == proposal
    assert feedback["formal_subclaims"][0]["lean_statement"] == (
        subclaim.lean_statement
    )
    assert feedback["lean_candidate_materialization"] == materialization
    assert manifest["decision"]["next_owner_subsystem"] == (
        "ArchitectCoordinator"
    )

    task = _formalizer_proof_state_routing_task(
        question=QUESTION,
        source_task=AgentTask(
            task_id="formalize:complete-proof-state",
            owner_subsystem="FormalizationEvaluator",
            objective="Check the exact source.",
            inputs={"theory_packet_id": "theory:complete-proof-state"},
        ),
        architect_context={},
        routing_manifest=manifest,
    )
    assert task is not None
    assert task.owner_subsystem == "ArchitectCoordinator"
    assert task.inputs["runtime_architect_operation"] == (
        "environment_feedback_route"
    )
    assert task.expected_artifacts == ("architect_feedback_route_decision",)
    serialized = json.dumps(task.inputs["environment_feedback"], sort_keys=True)
    assert "CriticEvaluator" not in serialized
    assert "GapPlanner" not in serialized
    assert "DIAGNOSTIC_TAIL" in serialized
    assert "GOAL_TAIL" in serialized
