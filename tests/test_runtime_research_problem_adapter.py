from __future__ import annotations

from types import SimpleNamespace

from ai_statistician.research_agent_runtime import _implementation_gaps
from ai_statistician.runtime_research_problem_adapter import (
    derive_runtime_research_problem,
    legacy_runtime_research_problem_provenance,
    runtime_llm_research_authority_required,
)
from ai_statistician.research_schema import OpenResearchQuestion


def _question() -> OpenResearchQuestion:
    return OpenResearchQuestion(
        id="operator_spectrum_frontier",
        title="Adaptive operator-spectrum inference",
        description=(
            "Develop an adaptive estimator and limit theorem for a compact "
            "operator spectrum under noisy indirect observations."
        ),
        tags=("operator", "spectrum"),
    )


def test_theory_packet_is_domain_general_research_authority() -> None:
    question = _question()
    packet = {
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory:operator-spectrum",
        "source_agent": "LLMTheoryDeveloperAgent",
        "provider": "anthropic",
        "model": "claude-sonnet-test",
        "ok": True,
        "problem_card": {
            "observed_data": "noisy linear functionals of an unknown operator",
            "dgp": "independent heteroskedastic measurement noise",
            "estimand": "the leading spectral projector",
            "assumptions": ["compactness", "a positive eigengap"],
            "asymptotic_regime": "sample size grows and noise level vanishes",
        },
        "theory_derivation_packet": {
            "assumption_ledger": [],
            "self_critique": ["The eigengap may shrink with sample size."],
        },
        "proof_plan": {
            "required_primitives": [
                "operator perturbation bound",
                "triangular-array central limit theorem",
            ]
        },
        "theorem_cards": [
            {
                "id": "spectral_limit",
                "informal_statement": "The adaptive projector has a Gaussian limit.",
                "proof_strategy": "linearize the spectral projector and control the remainder",
            }
        ],
        "simulation_ademp_spec": {
            "stress_tests": ["shrinking eigengap", "heteroskedastic noise"]
        },
    }

    bundle = derive_runtime_research_problem(
        question=question,
        architect_context={},
        theory_packet=packet,
    )

    assert bundle.problem.problem_class == "llm_structured_frontier_problem"
    assert bundle.problem.estimand == "the leading spectral projector"
    assert bundle.problem.assumptions == ("compactness", "a positive eigengap")
    assert bundle.problem.stress_tests == (
        "shrinking eigengap",
        "heteroskedastic noise",
    )
    assert bundle.theorem_goals[0].id == "spectral_limit"
    assert bundle.theorem_goals[0].status == "FORMAL_GAP"
    assert bundle.theorem_goals[0].proof_obligations == ()
    assert bundle.problem_formalization_source == (
        "theory_developer_structured_packet"
    )


def test_architect_plan_seeds_retrieval_without_task_family_classifier() -> None:
    question = _question()
    context = {
        "architect_coordinator_proposal_id": "architect:operator-spectrum",
        "architect_runtime_plan": {
            "problem_analysis": {
                "theorem_family": "adaptive spectral projector limit law",
                "statistical_objects": [
                    "noisy compact operator",
                    "leading spectral projector",
                ],
                "key_obstacles": ["shrinking eigengap"],
                "missing_information": ["available operator CLT lemmas"],
            },
            "stat_knowledge_bank_plan": {
                "assumption_dimensions": ["compactness", "eigengap"],
                "proof_skeletons_to_track": ["perturbation expansion"],
            },
            "evidence_contract": {
                "formal_targets": ["kernel-check the exact projector limit target"],
                "simulation_targets": ["stress a shrinking eigengap"],
            },
        },
    }

    assert runtime_llm_research_authority_required(context) is True
    bundle = derive_runtime_research_problem(
        question=question,
        architect_context=context,
    )

    assert bundle.problem.problem_class == "architect_defined_frontier_problem"
    assert bundle.problem.assumptions == ("compactness", "eigengap")
    assert bundle.theorem_goals[0].proof_obligations == ()
    assert bundle.problem_formalization_source == (
        "architect_coordinator_structured_plan"
    )


def test_legacy_mode_requires_explicit_absence_of_agentic_authority() -> None:
    assert runtime_llm_research_authority_required({}) is False
    assert runtime_llm_research_authority_required(
        {
            "runtime_requested_evidence_contract": {
                "evaluation_mode": "capability_eval"
            }
        }
    ) is True
    assert runtime_llm_research_authority_required(
        {"research_problem_authority_mode": "agentic"}
    ) is True
    assert runtime_llm_research_authority_required(
        {
            "research_problem_authority_mode": "legacy_baseline",
            "runtime_requested_evidence_contract": {
                "evaluation_mode": "capability_eval"
            },
        }
    ) is False
    assert legacy_runtime_research_problem_provenance() == {
        "problem_formalization_source": "legacy_keyword_problem_formalizer",
        "theorem_goal_source": "legacy_registered_theory_planner",
        "legacy_problem_formalizer_used": True,
        "legacy_theory_planner_used": True,
        "legacy_baseline_skipped_reason": "",
    }


def test_only_live_theory_packet_implicitly_activates_agentic_authority() -> None:
    packet = {
        "source_agent": "LLMTheoryDeveloperAgent",
        "provider": "anthropic",
        "model": "claude-sonnet-test",
        "ok": True,
        "problem_card": {"estimand": "a generic target"},
    }

    assert runtime_llm_research_authority_required({}, packet) is True
    assert runtime_llm_research_authority_required(
        {},
        {**packet, "provider": "static", "model": "fixture-model"},
    ) is False


def test_generated_algorithm_gate_does_not_accept_registered_template_match() -> None:
    packet = {"estimator_specs": [{"id": "known_template"}]}
    procedures = [
        SimpleNamespace(id="known_template", algorithm="known_template")
    ]

    assert _implementation_gaps(packet, procedures) == []
    gaps = _implementation_gaps(
        packet,
        procedures,
        require_generated_adapter=True,
    )

    assert [row["estimator_id"] for row in gaps] == ["known_template"]
    assert gaps[0]["status"] == (
        "REQUIRES_GENERATED_ALGORITHM_ENGINEER_ADAPTER"
    )
