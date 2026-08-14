from __future__ import annotations

import argparse
import asyncio
import json
import shutil
from pathlib import Path

import pytest

import ai_statistician.cli as cli_module
from ai_statistician.fingerprint import stable_hash
from ai_statistician.cli import (
    _apply_research_agent_runtime_evaluation_model_policy,
    _build_algorithm_engineer_agent_from_args,
    _build_architect_coordinator_agent_from_args,
    _build_critic_evaluator_agent_from_args,
    _build_generated_code_semantic_reviewer_agent_from_args,
    _build_formal_target_semantic_reviewer_agent_from_args,
    _build_formalizer_agent_from_args,
    _build_simulation_engineer_agent_from_args,
    _build_theory_generator_backend,
    build_parser,
    main,
)
from ai_statistician.structured_output_retry import PacketValidationError
from ai_statistician.estimator_interface_contract import (
    ESTIMATOR_REQUEST_BINDINGS,
    estimator_interface_contract_id,
    estimator_interface_contract_errors,
    normalize_estimator_interface_contract,
    theory_estimator_interface_contracts,
)
from ai_statistician.model_backend import (
    ClientToolCall,
    ClientToolTurnRequest,
    ClientToolTurnResponse,
    DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
    DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL,
    GeneratorRequest,
    GeneratorResponse,
    default_generator_model,
)
from ai_statistician.metric_protocol_stage import (
    build_theory_informed_metric_protocol_material,
)
from ai_statistician.research_architect import (
    KERNEL_PROOF_BOUNDARY,
    LLMTheoryDeveloperAgent,
    ResearchArchitectAgent,
    ResearchArchitectConfig,
    StaticArchitectLLMProvider,
    THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT,
    THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
    build_theory_developer_revision_inputs,
    build_theory_developer_prompt,
    validate_theory_core_packet,
    validate_theory_packet,
)
from ai_statistician.research_lab import load_open_research_questions
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.theory_proposal import GeneratorTheoryProposer
from ai_statistician.theory_revision_lineage import (
    THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY,
    build_theory_developer_revision_binding,
)
from ai_statistician.theory_workspace import (
    THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT,
    THEORY_WORKSPACE_GAP_TOOL,
    THEORY_WORKSPACE_WRITE_TOOL,
)


class SequentialGeneratorBackend:
    provider_name = "sequential_test"

    def __init__(self, responses: list[dict[str, object] | str]) -> None:
        self.responses = list(responses)
        self.requests: list[GeneratorRequest] = []

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("SequentialGeneratorBackend exhausted")
        response = self.responses.pop(0)
        text = json.dumps(response) if isinstance(response, dict) else response
        return GeneratorResponse(
            text=text,
            provider=self.provider_name,
            model=request.model,
            metadata={
                "generator_only": True,
                "tools_available": False,
                "provider_stop_reason": "end_turn",
            },
        )


def test_theory_core_contract_exposes_finite_execution_semantics() -> None:
    estimator_contract = THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT[
        "estimator_specs"
    ][0]

    assert "output_contract" in estimator_contract
    assert "termination_guarantee" in estimator_contract
    assert "estimator_interface_contract" not in estimator_contract


class ScriptedTheoryToolBackend:
    provider_name = "anthropic"

    def __init__(
        self,
        *,
        tool_responses: list[ClientToolTurnResponse],
        generator_responses: list[dict[str, object]],
    ) -> None:
        self.tool_responses = list(tool_responses)
        self.generator_responses = list(generator_responses)
        self.tool_requests: list[ClientToolTurnRequest] = []
        self.generator_requests: list[GeneratorRequest] = []

    def generate_client_tool_turn(
        self,
        request: ClientToolTurnRequest,
    ) -> ClientToolTurnResponse:
        self.tool_requests.append(request)
        if not self.tool_responses:
            raise AssertionError("ScriptedTheoryToolBackend tool responses exhausted")
        return self.tool_responses.pop(0)

    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        self.generator_requests.append(request)
        if not self.generator_responses:
            raise AssertionError(
                "ScriptedTheoryToolBackend generator responses exhausted"
            )
        return GeneratorResponse(
            text=json.dumps(self.generator_responses.pop(0)),
            provider=self.provider_name,
            model=request.model,
            metadata={
                "generator_only": True,
                "tools_available": False,
                "provider_stop_reason": "end_turn",
            },
        )


def _theory_tool_response(*calls: ClientToolCall) -> ClientToolTurnResponse:
    return ClientToolTurnResponse(
        content_blocks=tuple(
            {
                "type": "tool_use",
                "id": call.call_id,
                "name": call.name,
                "input": dict(call.input),
            }
            for call in calls
        ),
        tool_calls=tuple(calls),
        text="",
        provider="anthropic",
        model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
        metadata={"provider_stop_reason": "tool_use"},
    )


def _theory_artifact_writes(
    artifacts: dict[str, object],
) -> dict[str, object]:
    return {
        "writes": [
            {"artifact_name": name, "value": value}
            for name, value in artifacts.items()
        ]
    }


class ProviderWithoutIdentity:
    def generate(self, request: GeneratorRequest) -> GeneratorResponse:
        return GeneratorResponse(text="{}", provider="", model=request.model)


def _sample_response() -> dict[str, object]:
    return {
        "problem_card": {
            "observed_data": "i.i.d. observations O_i=(X_i,A_i,Y_i)",
            "dgp": "semiparametric observed-data law with binary treatment",
            "estimand": "psi = E[m_1(X)-m_0(X)]",
            "nuisance_quantities": ["m_a(x)", "e(x)"],
            "assumptions": ["consistency", "conditional exchangeability", "positivity"],
            "asymptotic_regime": "n -> infinity with nuisance product-rate control",
            "desired_theorem_type": "asymptotic linearity and normality",
        },
        "theory_derivation_packet": {
            "derivation_summary": "Use Neyman-orthogonal AIPW score for the ATE.",
            "derivation_steps": [
                {
                    "id": "identify_ate",
                    "claim": "Conditional exchangeability identifies the ATE by nuisance regressions.",
                    "equation_or_argument": "psi = E[m_1(X)-m_0(X)]",
                    "depends_on": [],
                    "formal_goal": "aipw_asymptotic_normality",
                    "risk": "consistency and positivity must be stated explicitly",
                },
                {
                    "id": "orthogonal_score",
                    "claim": "AIPW score has first-order insensitivity to nuisance error.",
                    "equation_or_argument": "phi = m1-m0 + A/e(Y-m1) - (1-A)/(1-e)(Y-m0) - psi",
                    "depends_on": ["identify_ate"],
                    "formal_goal": "second_order_remainder_bound",
                    "risk": "positivity and integrability are required",
                },
                {
                    "id": "remainder_control",
                    "claim": "Cross-fitting plus product-rate nuisance control makes the second-order remainder negligible.",
                    "equation_or_argument": "sqrt(n)(P_n phi_hat - P_n phi) = o_p(1)",
                    "depends_on": ["orthogonal_score"],
                    "formal_goal": "aipw_asymptotic_normality",
                    "risk": "empirical-process conditions are not yet formalized",
                },
            ],
            "equation_chain": [
                {
                    "step_id": "identified_estimand",
                    "lhs": "psi",
                    "relation": "=",
                    "rhs": "E[m_1(X)-m_0(X)]",
                    "justification": "identification under consistency and exchangeability",
                    "depends_on": ["identify_ate"],
                },
                {
                    "step_id": "orthogonal_expansion",
                    "lhs": "sqrt(n)(psi_hat-psi)",
                    "relation": "=",
                    "rhs": "sqrt(n) P_n phi + o_p(1)",
                    "justification": "AIPW orthogonality and cross-fit remainder control",
                    "depends_on": ["orthogonal_score", "remainder_control"],
                },
            ],
            "assumption_ledger": [
                {
                    "assumption": "conditional exchangeability",
                    "role": "identification",
                    "used_in": ["identify_ate", "identified_estimand"],
                    "risk_if_dropped": "ATE identification fails",
                },
                {
                    "assumption": "positivity",
                    "role": "regularity",
                    "used_in": ["orthogonal_score"],
                    "risk_if_dropped": "inverse propensity weights can diverge",
                },
                {
                    "assumption": "product-rate nuisance convergence",
                    "role": "regularity",
                    "used_in": ["remainder_control", "orthogonal_expansion"],
                    "risk_if_dropped": "second-order remainder may dominate",
                },
            ],
            "sanity_checks": [
                {
                    "id": "check_identification",
                    "claim_ref": "identified_estimand",
                    "check_type": "direct_substitution",
                    "recomputation": (
                        "Substitute the conditional means into the g-formula."
                    ),
                    "result": "PASS: psi = E[m_1(X)-m_0(X)]",
                    "depends_on": ["identify_ate"],
                },
                {
                    "id": "check_positivity",
                    "claim_ref": "orthogonal_score",
                    "check_type": "boundary_case",
                    "recomputation": (
                        "Let e(X) approach zero in A/e(X); the weight diverges."
                    ),
                    "result": (
                        "PASS: A positive lower propensity bound is required."
                    ),
                    "depends_on": ["orthogonal_score"],
                },
                {
                    "id": "check_remainder_scale",
                    "claim_ref": "orthogonal_expansion",
                    "check_type": "uncertainty_scale",
                    "recomputation": (
                        "Multiply two o_p(n^-1/4) nuisance errors."
                    ),
                    "result": "PASS: Their product is o_p(n^-1/2).",
                    "depends_on": ["remainder_control"],
                },
            ],
            "formalization_handoff": {
                "source_theorem_target": "aipw_asymptotic_normality",
                "candidate_lean_targets": ["bounded_aipw_expansion"],
                "required_definitions": ["conditional_exchangeability", "aipw_score"],
                "lemma_dependencies": ["second_order_remainder_bound"],
                "semantic_alignment_constraints": ["do not drop nuisance remainder"],
            },
            "self_critique": ["Product-rate assumptions may be too strong for adaptive learners."],
            "rejected_alternatives": [
                {"name": "IPW only", "reason": "unstable under near-positivity violations"}
            ],
        },
        "estimator_specs": [
            {
                "id": "crossfit_aipw",
                "name": "cross-fitted AIPW",
                "formula": "P_n phi_hat + psi_hat",
                "algorithm_sketch": "fit nuisances on folds and evaluate held-out scores",
                "inputs": ["one observed sample of O_i=(X_i,A_i,Y_i)"],
                "outputs": ["cross-fitted AIPW estimate of psi"],
                "normalization": "finite-sample point estimate",
                "sample_size_order": "O_p(1)",
                "tuning": ["number of folds"],
                "required_assumptions": ["positivity", "product-rate nuisance convergence"],
                "estimator_interface_contract": {
                    "request_fields": [
                        {
                            "name": "observations",
                            "meaning": "one replicate of observed O_i=(X_i,A_i,Y_i)",
                            "binding": "per_replicate_data",
                        }
                    ],
                    "response_fields": [
                        {
                            "name": "estimate",
                            "meaning": "cross-fitted AIPW estimate of psi",
                            "normalization": "finite-sample point estimate, not root-n scaled",
                            "sample_size_order": "O(1)",
                            "sample_size_rate": {
                                "scale": "constant",
                                "index_symbol": "n",
                                "polynomial_exponent": 0.0,
                                "log_exponent": 0.0,
                                "contributions": [
                                    {
                                        "quantity": "finite point-estimate scale",
                                        "polynomial_exponent": 0.0,
                                        "log_exponent": 0.0,
                                        "justification_ref": "orthogonal_expansion",
                                    }
                                ],
                            },
                            "derivation_ref": "orthogonal_expansion",
                        }
                    ],
                },
            }
        ],
        "theorem_cards": [
            {
                "id": "aipw_asymptotic_normality",
                "informal_statement": "Under consistency, exchangeability, positivity, and nuisance rates, cross-fitted AIPW is asymptotically normal.",
                "assumptions_used": ["consistency", "exchangeability", "positivity"],
                "conclusion": "sqrt(n)(psi_hat-psi) -> N(0, Var(phi))",
                "rate_or_limit_law": "root-n CLT",
                "proof_strategy": "show influence-function expansion plus negligible second-order remainder",
                "semantic_risks": ["formalizing conditional exchangeability faithfully"],
            }
        ],
        "lemma_cards": [
            {
                "id": "second_order_remainder_bound",
                "statement": "The product of nuisance errors bounds the AIPW remainder.",
                "depends_on": ["orthogonal_score"],
                "used_by": ["aipw_asymptotic_normality"],
                "formalization_difficulty": "high",
            }
        ],
        "proof_plan": {
            "proof_dependency_dag": [
                {"from": "second_order_remainder_bound", "to": "aipw_asymptotic_normality"}
            ],
            "required_primitives": ["conditional_expectation", "slutsky_theorem"],
            "acceptable_strengthening": ["bounded outcomes for first Lean target"],
            "unacceptable_changes": ["replace conditional exchangeability with randomized treatment"],
        },
        "formalization_requests": [
            {
                "id": "lean_aipw_asymptotic_normality",
                "target_theorem_card": "aipw_asymptotic_normality",
                "lean_statement_sketch": "theorem aipw_asymptotic_normality ...",
                "semantic_alignment_constraints": ["do not drop nuisance remainder"],
                "kernel_status": "OPEN",
            }
        ],
        "simulation_ademp_spec": {
            "aim": "stress AIPW coverage under nuisance misspecification",
            "dgps": ["well-overlapped", "near-positivity violation"],
            "methods": ["crossfit_aipw", "ipw_only"],
            "performance_measures": ["bias", "rmse", "coverage_95"],
            "stress_tests": ["propensity scores close to zero"],
            "expected_theoretical_behavior": ["coverage approaches nominal under overlap"],
        },
        "critic_findings": [
            {
                "critic": "assumption_critic",
                "finding": "positivity must be quantified with a lower bound",
                "reroute_if_confirmed": "TheoryDeveloper",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "Formalizer",
                "action": "formalize bounded-outcome AIPW expansion target",
                "acceptance_gate": "Lean statement semantic review then kernel proof attempt",
            }
        ],
    }


def _serious_sample_response() -> dict[str, object]:
    response = json.loads(json.dumps(_sample_response()))
    derivation = dict(response["theory_derivation_packet"])
    derivation_steps = list(derivation["derivation_steps"])
    derivation_steps.extend(
        [
            {
                "id": "limit_variance",
                "claim": "The influence-function variance determines the root-n limit.",
                "equation_or_argument": "Var(phi)=E[phi^2] under E[phi]=0",
                "depends_on": ["orthogonal_score"],
                "formal_goal": "aipw_limit_variance",
                "risk": "finite second moments are required",
            },
            {
                "id": "studentized_limit",
                "claim": "A consistent variance estimate yields studentized normality.",
                "equation_or_argument": "sqrt(n)(psi_hat-psi)/sigma_hat => N(0,1)",
                "depends_on": ["remainder_control", "limit_variance"],
                "formal_goal": "aipw_studentized_normality",
                "risk": "variance consistency needs a separate lemma",
            },
        ]
    )
    derivation["derivation_steps"] = derivation_steps
    equation_chain = list(derivation["equation_chain"])
    equation_chain.extend(
        [
            {
                "step_id": "variance_identity",
                "lhs": "sigma^2",
                "relation": "=",
                "rhs": "E[phi^2]",
                "justification": "the centered influence function has mean zero",
                "depends_on": ["limit_variance"],
            },
            {
                "step_id": "studentized_expansion",
                "lhs": "sqrt(n)(psi_hat-psi)/sigma_hat",
                "relation": "=",
                "rhs": "sqrt(n)P_n phi/sigma + o_p(1)",
                "justification": "Slutsky after remainder and variance control",
                "depends_on": ["studentized_limit"],
            },
        ]
    )
    derivation["equation_chain"] = equation_chain
    response["theory_derivation_packet"] = derivation
    return response


def _metric_theory_revision_context(
    *,
    question: OpenResearchQuestion,
    parent: dict[str, object],
) -> dict[str, object]:
    source_packet_id = "theory_derivation:targeted-revision-parent"
    material = build_theory_informed_metric_protocol_material(
        theory_packet=parent,
        theory_packet_id=source_packet_id,
    )
    feedback = {
        "artifact_kind": "RuntimeMetricProtocolPreExecutionReviewObservation",
        "feedback_id": "metric-protocol-theory-feedback:targeted",
        "question_id": question.id,
        "source_theory_packet_id": source_packet_id,
        "source_theory_packet_hash": material["source_theory_packet_hash"],
        "source_metric_protocol_rejection_manifest_id": "metric-rejection:targeted",
        "execution_authorized": False,
        "upstream_theory_revision_count": 1,
        "max_upstream_theory_revisions": 2,
        "architect_route_required": True,
        "runtime_selected_owner": False,
        "findings": [
            {
                "finding_id": "metric_protocol_finding:bounded-outcome",
                "severity": "high",
                "category": "assumption audit",
                "summary": "The bounded-outcome premise is not explicit.",
                "observed_behavior": "The premise is implicit in the current derivation.",
                "expected_behavior": "The premise is explicit and referenced by dependents.",
            }
        ],
        "active_unresolved_finding_ids": [
            "metric_protocol_finding:bounded-outcome"
        ],
        "acceptance_gate": "Fresh theory must pass independent metric review.",
    }
    return {
        "environment_feedback": feedback,
        "metric_protocol_prior_theory_material": material,
    }


def test_research_architect_records_llm_theory_packet_and_evidence_ledger() -> None:
    out_dir = Path("runs/test_research_architect")
    shutil.rmtree(out_dir, ignore_errors=True)
    question = OpenResearchQuestion(
        id="ate_open",
        title="AIPW ATE",
        description="Derive an estimator and theorem for an observational ATE.",
        tags=("causal",),
    )
    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(_sample_response()),
        config=ResearchArchitectConfig(provider_name="static", model="static-theory-model"),
    )
    manifest = ResearchArchitectAgent(
        theory_developer=developer,
        out_dir=out_dir,
    ).run_theory_development([question])

    assert manifest["all_packets_ok"]
    assert manifest["proof_evidence_status"] == THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet_path = out_dir / "theory_derivation_packets.jsonl"
    ledger_path = out_dir / "evidence_ledger.jsonl"
    state_path = out_dir / "architect_project_state.json"
    assert packet_path.exists()
    assert ledger_path.exists()
    assert state_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8").splitlines()[0])
    ledger = json.loads(ledger_path.read_text(encoding="utf-8").splitlines()[0])
    assert packet["source_agent"] == "LLMTheoryDeveloperAgent"
    assert packet["theory_derivation_packet"]["derivation_steps"]
    assert packet["theory_derivation_contract"]["n_derivation_steps"] == 3
    assert packet["theory_derivation_contract"]["n_equation_chain_steps"] == 2
    assert packet["theory_derivation_contract"]["n_assumption_ledger_rows"] == 3
    assert packet["theory_derivation_contract"]["has_formalization_handoff"] is True
    assert packet["kernel_verified"] is False
    assert ledger["evidence_status"] == "PROPOSAL_RECORDED_REQUIRES_GATES"
    assert ledger["boundary"] == KERNEL_PROOF_BOUNDARY


def test_llm_theory_developer_validation_rejects_empty_required_structures() -> None:
    bad = _sample_response()
    derivation = dict(bad["theory_derivation_packet"])
    derivation["derivation_steps"] = []
    derivation["equation_chain"] = []
    derivation["assumption_ledger"] = []
    derivation["formalization_handoff"] = {}
    bad["theory_derivation_packet"] = derivation
    bad["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    bad["kernel_verified"] = False

    errors = validate_theory_packet(bad)

    assert any("derivation_steps" in error for error in errors)
    assert any("equation_chain" in error for error in errors)
    assert any("assumption_ledger" in error for error in errors)
    assert any("formalization_handoff" in error for error in errors)


def test_theory_validation_rejects_dangling_formal_target_references() -> None:
    bad = _sample_response()
    theorem_cards = [dict(row) for row in bad["theorem_cards"]]
    theorem_cards.append(dict(theorem_cards[0]))
    bad["theorem_cards"] = theorem_cards
    derivation = dict(bad["theory_derivation_packet"])
    handoff = dict(derivation["formalization_handoff"])
    handoff["source_theorem_target"] = "invented_aggregate_alias"
    derivation["formalization_handoff"] = handoff
    bad["theory_derivation_packet"] = derivation
    requests = [dict(row) for row in bad["formalization_requests"]]
    requests[0]["target_theorem_card"] = "missing_theorem_card"
    bad["formalization_requests"] = requests

    errors = validate_theory_core_packet(bad)

    assert "theorem_cards ids must be unique" in errors
    assert any(
        "source_theorem_target must exactly match a theorem_cards id" in error
        and "invented_aggregate_alias" in error
        for error in errors
    )
    assert any(
        "formalization_requests[0].target_theorem_card must exactly match"
        in error
        and "missing_theorem_card" in error
        for error in errors
    )


def test_theory_validation_allows_model_selected_supporting_row_counts() -> None:
    packet = _sample_response()
    derivation = dict(packet["theory_derivation_packet"])
    derivation["derivation_steps"] = derivation["derivation_steps"][:1]
    derivation["equation_chain"] = derivation["equation_chain"][:1]
    derivation["sanity_checks"] = derivation["sanity_checks"][:1]
    packet["theory_derivation_packet"] = derivation
    packet["lemma_cards"] = []
    packet["critic_findings"] = []
    packet["next_actions"] = []
    packet["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet["kernel_verified"] = False

    assert validate_theory_core_packet(packet) == []


def test_advisory_theory_can_omit_formalization_authoring_artifacts() -> None:
    packet = _sample_response()
    derivation = dict(packet["theory_derivation_packet"])
    derivation.pop("formalization_handoff")
    packet["theory_derivation_packet"] = derivation
    packet["formalization_requests"] = []
    packet["runtime_formalization_authoring_required"] = False
    packet["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet["kernel_verified"] = False

    assert validate_theory_core_packet(packet) == []


def test_optional_theory_prompt_does_not_invent_formalization_work() -> None:
    prompt = build_theory_developer_prompt(
        OpenResearchQuestion(
            id="optional_formalization",
            title="Optional formalization",
            description="Develop and test a statistical procedure.",
        ),
        architect_context={
            "runtime_requested_evidence_contract": {
                "evaluation_mode": "research_eval",
                "formal_target_authoring_required": False,
            }
        },
    )
    payload = json.loads(prompt.split("\n\n", 1)[1])

    assert payload["concise_output_budget"]["max_formalization_requests"] == 0
    assert payload["required_output_contract"]["formalization_requests"] == []
    assert payload["required_output_contract"]["theory_derivation_packet"][
        "formalization_handoff"
    ] == {}
    assert "Leave formalization artifacts empty" in prompt


def test_runtime_formal_contract_cannot_be_lowered_by_architect_plan() -> None:
    prompt = build_theory_developer_prompt(
        OpenResearchQuestion(
            id="strict_formalization",
            title="Strict formalization",
            description="Exercise the strict integrated proof capability.",
        ),
        architect_context={
            "runtime_requested_evidence_contract": {
                "evaluation_mode": "capability_eval",
                "formal_target_authoring_required": True,
            },
            "architect_runtime_plan": {
                "evidence_contract": {
                    "evaluation_mode": "research_eval",
                    "formal_target_authoring_required": False,
                }
            },
        },
    )
    payload = json.loads(prompt.split("\n\n", 1)[1])

    assert payload["serious_theory_output_budget"][
        "max_formalization_requests"
    ] > 0
    assert payload["required_output_contract"]["formalization_requests"]
    assert "Keep the formal target consistent" in prompt


def test_theory_validation_preserves_an_unresolved_sanity_check_for_review() -> None:
    packet = _sample_response()
    derivation = dict(packet["theory_derivation_packet"])
    sanity_checks = [dict(row) for row in derivation["sanity_checks"]]
    sanity_checks[0]["result"] = (
        "FAIL: the recomputation contradicts the authoritative derivation"
    )
    derivation["sanity_checks"] = sanity_checks
    packet["theory_derivation_packet"] = derivation
    packet["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet["kernel_verified"] = False

    assert validate_theory_core_packet(packet) == []


def test_theory_contract_keeps_model_authored_sanity_dispositions() -> None:
    sanity_contract = THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT[
        "theory_derivation_packet"
    ]["sanity_checks"][0]

    assert "PASS|FAIL|INCONCLUSIVE" in sanity_contract["result"]
    assert "conclusion" not in sanity_contract


def test_theory_validation_requires_operational_precode_semantics() -> None:
    bad = _sample_response()
    problem_card = dict(bad["problem_card"])
    problem_card["dgp"] = ""
    bad["problem_card"] = problem_card
    derivation = dict(bad["theory_derivation_packet"])
    assumption_ledger = [
        dict(row) for row in derivation["assumption_ledger"]
    ]
    assumption_ledger[0]["role"] = "martingale measurability"
    derivation["assumption_ledger"] = assumption_ledger
    bad["theory_derivation_packet"] = derivation
    estimator_specs = [dict(row) for row in bad["estimator_specs"]]
    estimator_specs[0]["formula"] = ""
    bad["estimator_specs"] = estimator_specs
    ademp = dict(bad["simulation_ademp_spec"])
    ademp["dgps"] = []
    bad["simulation_ademp_spec"] = ademp
    bad["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    bad["kernel_verified"] = False

    errors = validate_theory_packet(bad)

    assert "problem_card.dgp must be non-empty" in errors
    assert not any("role" in error for error in errors)
    assert "estimator_specs[0].formula must be non-empty" in errors
    assert "simulation_ademp_spec.dgps must be a non-empty list" in errors


def test_theory_validation_rejects_unresolved_estimator_semantic_reference() -> None:
    packet = _sample_response()
    estimator = dict(packet["estimator_specs"][0])
    contract = dict(estimator["estimator_interface_contract"])
    response_fields = [dict(row) for row in contract["response_fields"]]
    response_fields[0]["derivation_ref"] = "missing_theory_step"
    contract["response_fields"] = response_fields
    estimator["estimator_interface_contract"] = contract
    estimator["estimator_interface_contract_id"] = (
        estimator_interface_contract_id(contract)
    )
    packet["estimator_specs"] = [estimator]
    packet["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet["kernel_verified"] = False

    errors = validate_theory_packet(packet)

    unresolved = next(
        row
        for row in errors
        if "unresolved derivation_ref missing_theory_step" in row
    )
    assert "choose exactly one allowed reference id from:" in unresolved
    assert "orthogonal_expansion" in unresolved


def test_theory_validation_reports_allowed_rate_justification_references() -> None:
    packet = _sample_response()
    estimator = dict(packet["estimator_specs"][0])
    contract = dict(estimator["estimator_interface_contract"])
    response_fields = [dict(row) for row in contract["response_fields"]]
    rate = dict(response_fields[0]["sample_size_rate"])
    contributions = [dict(row) for row in rate["contributions"]]
    contributions[0]["justification_ref"] = "missing_theory_step"
    rate["contributions"] = contributions
    response_fields[0]["sample_size_rate"] = rate
    contract["response_fields"] = response_fields
    estimator["estimator_interface_contract"] = contract
    estimator["estimator_interface_contract_id"] = (
        estimator_interface_contract_id(contract)
    )
    packet["estimator_specs"] = [estimator]
    packet["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet["kernel_verified"] = False

    errors = validate_theory_packet(packet)

    unresolved = next(
        row
        for row in errors
        if "unresolved justification_ref missing_theory_step" in row
    )
    assert "choose exactly one allowed reference id from:" in unresolved
    assert "orthogonal_expansion" in unresolved


def test_theory_validation_accepts_existing_lemma_as_interface_justification() -> None:
    packet = _sample_response()
    estimator = dict(packet["estimator_specs"][0])
    contract = dict(estimator["estimator_interface_contract"])
    response_fields = [dict(row) for row in contract["response_fields"]]
    response_fields[0]["derivation_ref"] = "second_order_remainder_bound"
    rate = dict(response_fields[0]["sample_size_rate"])
    contributions = [dict(row) for row in rate["contributions"]]
    contributions[0]["justification_ref"] = "second_order_remainder_bound"
    rate["contributions"] = contributions
    response_fields[0]["sample_size_rate"] = rate
    contract["response_fields"] = response_fields
    estimator["estimator_interface_contract"] = contract
    estimator["estimator_interface_contract_id"] = (
        estimator_interface_contract_id(contract)
    )
    packet["estimator_specs"] = [estimator]
    packet["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet["kernel_verified"] = False

    errors = validate_theory_packet(packet)

    assert not any("unresolved derivation_ref" in row for row in errors)
    assert not any("unresolved justification_ref" in row for row in errors)


def test_theory_validation_does_not_invent_rate_composition_rule() -> None:
    packet = _sample_response()
    estimator = dict(packet["estimator_specs"][0])
    contract = dict(estimator["estimator_interface_contract"])
    response_fields = [dict(row) for row in contract["response_fields"]]
    rate = dict(response_fields[0]["sample_size_rate"])
    rate["polynomial_exponent"] = -1.0
    response_fields[0]["sample_size_rate"] = rate
    contract["response_fields"] = response_fields
    estimator["estimator_interface_contract"] = contract
    estimator["estimator_interface_contract_id"] = (
        estimator_interface_contract_id(contract)
    )
    packet["estimator_specs"] = [estimator]
    packet["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet["kernel_verified"] = False

    errors = validate_theory_packet(packet)

    assert not any("sum of signed contributions" in error for error in errors)


def test_interface_normalization_preserves_model_authored_rate() -> None:
    contract = json.loads(
        json.dumps(
            _sample_response()["estimator_specs"][0][
                "estimator_interface_contract"
            ]
        )
    )
    rate = contract["response_fields"][0]["sample_size_rate"]
    rate["polynomial_exponent"] = 99.0
    rate["log_exponent"] = -99.0
    rate["contributions"] = [
        {
            "quantity": "aggregation over the primary index",
            "polynomial_exponent": 1.0,
            "log_exponent": 0.0,
            "justification_ref": "orthogonal_expansion",
        },
        {
            "quantity": "normalization by the primary index",
            "polynomial_exponent": -1.0,
            "log_exponent": 0.5,
            "justification_ref": "orthogonal_expansion",
        },
    ]

    normalized = normalize_estimator_interface_contract(contract)
    normalized_rate = normalized["response_fields"][0]["sample_size_rate"]

    assert normalized_rate["polynomial_exponent"] == 99.0
    assert normalized_rate["log_exponent"] == -99.0
    assert normalized_rate["contributions"] == rate["contributions"]


def test_not_indexed_interface_rate_has_no_synthetic_exponents() -> None:
    contract = json.loads(
        json.dumps(
            _sample_response()["estimator_specs"][0][
                "estimator_interface_contract"
            ]
        )
    )
    contract["response_fields"][0]["sample_size_rate"] = {
        "scale": "not_indexed"
    }

    assert estimator_interface_contract_errors(
        contract,
        label="interface",
        required=True,
        require_typed_rate=True,
    ) == []

    contract["response_fields"][0]["sample_size_rate"][
        "polynomial_exponent"
    ] = 0.0
    assert any(
        "must not carry synthetic rate fields" in error
        for error in estimator_interface_contract_errors(
            contract,
            label="interface",
            required=True,
            require_typed_rate=True,
        )
    )
    normalized = normalize_estimator_interface_contract(contract)
    assert normalized["response_fields"][0]["sample_size_rate"] == (
        contract["response_fields"][0]["sample_size_rate"]
    )


def test_theory_interface_boundary_does_not_silently_repair_legacy_rate() -> None:
    packet = _sample_response()
    contract = packet["estimator_specs"][0]["estimator_interface_contract"]
    contract["response_fields"][0]["sample_size_rate"] = {
        "scale": "not_indexed",
        "index": "none",
        "polynomial_exponent": 0.0,
        "log_exponent": 0.0,
        "contributions": [],
    }

    rows = theory_estimator_interface_contracts(packet)
    canonical = rows["crossfit_aipw"]["contract"]

    assert canonical["response_fields"][0]["sample_size_rate"] == (
        contract["response_fields"][0]["sample_size_rate"]
    )
    assert rows["crossfit_aipw"]["contract_id"] == (
        estimator_interface_contract_id(canonical)
    )


def test_serious_theory_validation_requires_explicit_sanity_recomputations() -> None:
    packet = _sample_response()
    derivation = dict(packet["theory_derivation_packet"])
    derivation.pop("sanity_checks")
    packet["theory_derivation_packet"] = derivation
    packet["serious_theory_mode"] = True
    packet["proof_evidence_status"] = THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    packet["kernel_verified"] = False

    errors = validate_theory_packet(packet)

    assert any("sanity_checks must be a non-empty list" in error for error in errors)


def test_capability_theory_mode_uses_reviewer_owned_rigor_not_row_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "claude-sonnet-serious-theory-test",
    )
    provider = SequentialGeneratorBackend([_sample_response()])
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            max_validation_retries=0,
        ),
    )

    packet = developer.derive(
        OpenResearchQuestion(
            id="serious_theory",
            title="Serious theory mode",
            description="Require a research-grade equation trace.",
        ),
        architect_context={
            "architect_runtime_plan": {
                "evidence_contract": {"evaluation_mode": "capability_eval"}
            }
        },
    )

    assert packet["ok"] is True
    assert packet["theory_derivation_contract"]["row_count_policy"] == (
        "model_selected_nonempty_required_structures"
    )
    assert len(provider.requests) == 1
    request = provider.requests[0]
    assert request.model == "claude-sonnet-serious-theory-test"
    assert request.max_tokens == 10000
    assert request.metadata["model_tier"] == "sonnet"
    assert request.metadata["base_model_tier"] == "sonnet"
    assert request.metadata["serious_theory_mode"] is True
    assert request.metadata["theory_prompt_mode"] == (
        "serious_capability_theory_workspace"
    )
    derivation_schema = request.schema["properties"][
        "theory_derivation_packet"
    ]["properties"]
    assert derivation_schema["derivation_steps"]["minItems"] == 1
    assert derivation_schema["equation_chain"]["minItems"] == 1
    assert derivation_schema["sanity_checks"]["minItems"] == 1
    assert derivation_schema["derivation_steps"]["maxItems"] == 8
    assert derivation_schema["equation_chain"]["maxItems"] == 8
    assert derivation_schema["sanity_checks"]["maxItems"] == 6
    assert request.schema["properties"]["theorem_cards"]["maxItems"] == 2
    assert request.schema["properties"]["problem_card"]["properties"][
        "observed_data"
    ]["maxLength"] == 420
    assert "You own all mathematical content" in request.user_prompt
    assert "runtime does not provide issue-specific corrections" in (
        request.user_prompt
    )
    assert "reviewer observations as evidence" in request.user_prompt
    assert "row counts are not a quality metric" in request.user_prompt
    assert "n or sqrt(n) factor" not in request.user_prompt
    assert "one-observation or boundary value" not in request.user_prompt
    assert "optimization, extrema, stopping" not in request.user_prompt


def test_theory_developer_anthropic_request_uses_structured_output() -> None:
    class AnthropicReplayBackend(SequentialGeneratorBackend):
        provider_name = "anthropic"

    provider = AnthropicReplayBackend([_sample_response()])
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )

    packet = developer.derive(
        OpenResearchQuestion(
            id="structured_output",
            title="Structured output",
            description="Exercise the provider-native theory packet contract.",
        )
    )

    assert packet["ok"] is True
    estimator = packet["estimator_specs"][0]
    assert estimator["estimator_interface_contract_id"] == (
        estimator_interface_contract_id(
            estimator["estimator_interface_contract"]
        )
    )
    assert provider.requests[0].metadata["provider_structured_output"] is True
    assert provider.requests[0].schema is not None
    estimator_schema = provider.requests[0].schema["properties"][
        "estimator_specs"
    ]["items"]
    assert "estimator_interface_contract" not in estimator_schema["properties"]
    assert "estimator_interface_contract" not in estimator_schema["required"]
    assert provider.requests[0].metadata["theory_developer_phase"] == (
        "core_theory_workspace"
    )
    assert len(provider.requests) == 1


def test_live_initial_theory_uses_model_owned_artifact_workspace() -> None:
    question = OpenResearchQuestion(
        id="initial_theory_workspace",
        title="Initial theory workspace",
        description="Author initial theory through direct model-owned artifacts.",
    )
    core_response = _sample_response()
    core_estimators = [dict(row) for row in core_response["estimator_specs"]]
    expected_contract = core_estimators[0].pop(
        "estimator_interface_contract"
    )
    core_response["estimator_specs"] = core_estimators
    optional_artifacts = {"lemma_cards", "critic_findings", "next_actions"}
    for field in optional_artifacts:
        core_response[field] = []
    core_artifacts = {
        field: core_response[field]
        for field in THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT
        if field not in optional_artifacts
    }
    invalid_core_artifacts = json.loads(json.dumps(core_artifacts))
    invalid_core_artifacts["theory_derivation_packet"][
        "formalization_handoff"
    ]["source_theorem_target"] = "invented_aggregate_alias"
    fixed_derivation = json.loads(
        json.dumps(invalid_core_artifacts["theory_derivation_packet"])
    )
    fixed_derivation["formalization_handoff"][
        "source_theorem_target"
    ] = "aipw_asymptotic_normality"
    initial_artifact_items = list(invalid_core_artifacts.items())
    initial_artifact_batches = [
        dict(initial_artifact_items[index : index + 2])
        for index in range(0, len(initial_artifact_items), 2)
    ]
    provider = ScriptedTheoryToolBackend(
        tool_responses=[
            _theory_tool_response(
                ClientToolCall(
                    call_id="read-initial-context",
                    name="read_theory_workspace",
                    input={
                        "artifact_names": ["initial_authoring_context"]
                    },
                )
            ),
            *[
                _theory_tool_response(
                    ClientToolCall(
                        call_id=f"edit-initial-theory-{index}",
                        name=THEORY_WORKSPACE_WRITE_TOOL,
                        input=_theory_artifact_writes(batch),
                    )
                )
                for index, batch in enumerate(initial_artifact_batches)
            ],
            _theory_tool_response(
                ClientToolCall(
                    call_id="reread-theory-before-fix",
                    name="read_theory_workspace",
                    input={
                        "artifact_names": ["theory_derivation_packet"]
                    },
                )
            ),
            _theory_tool_response(
                ClientToolCall(
                    call_id="fix-formal-target-reference",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_theory_artifact_writes(
                        {"theory_derivation_packet": fixed_derivation}
                    ),
                )
            ),
        ],
        generator_responses=[
            {
                "interfaces": {
                    core_estimators[0]["id"]: expected_contract
                }
            }
        ],
    )
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )

    packet = developer.derive(question)

    assert validate_theory_packet(packet) == []
    assert len(provider.tool_requests) == 7
    assert len(provider.generator_requests) == 1
    first_request = provider.tool_requests[0]
    assert first_request.metadata["theory_developer_phase"] == (
        "initial_artifact_workspace"
    )
    assert first_request.metadata["authoring_mode"] == (
        "model_owned_artifact_workspace"
    )
    assert {tool.name for tool in first_request.tools} == {
        "read_theory_workspace",
        THEORY_WORKSPACE_WRITE_TOOL,
        THEORY_WORKSPACE_GAP_TOOL,
    }
    initial_prompt = str(first_request.messages[0]["content"])
    assert core_response["problem_card"]["dgp"] not in initial_prompt
    assert "Authoritative theory workspace catalog" in initial_prompt
    assert "initial_authoring_context" in initial_prompt
    assert (
        f"at most {developer.config.theory_workspace_max_submissions} writes"
        in initial_prompt
    )
    assert question.description in str(provider.tool_requests[1].messages)
    assert "desired_theorem_type" in str(
        provider.tool_requests[1].messages
    )
    assert (
        "source_theorem_target must exactly match a theorem_cards id"
        in str(provider.tool_requests[-1].messages)
    )
    assert "invented_aggregate_alias" in str(
        provider.tool_requests[-1].messages
    )
    assert packet["problem_card"]["dgp"] == core_response["problem_card"][
        "dgp"
    ]
    evidence = packet["llm_client_tool_loop"]
    assert evidence["workspace_operation"] == "initial_discovery"
    assert evidence["write_transport"] == (
        THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT
    )
    assert evidence["n_model_artifact_writes"] == len(core_artifacts) + 1
    assert evidence["model_owned_theory"] is True
    assert evidence["runtime_edited_theory"] is False
    assert evidence["reads"] == 2
    assert evidence["submissions"] == 5
    assert set(evidence["changed_artifact_names"]) == (
        set(THEORY_DEVELOPER_CORE_OUTPUT_CONTRACT) - optional_artifacts
    )
    assert packet["lemma_cards"] == []
    assert packet["critic_findings"] == []
    assert packet["next_actions"] == []
    assert packet["theory_generation_phases"][0]["phase"] == (
        "initial_artifact_workspace"
    )
    assert provider.generator_requests[0].metadata[
        "theory_developer_phase"
    ] == "estimator_interface_authoring"


def test_theory_developer_authors_interfaces_after_freezing_core_theory() -> None:
    class AnthropicReplayBackend(SequentialGeneratorBackend):
        provider_name = "anthropic"

    core_response = _sample_response()
    core_estimators = [dict(row) for row in core_response["estimator_specs"]]
    expected_contract = core_estimators[0].pop("estimator_interface_contract")
    core_response["estimator_specs"] = core_estimators
    interface_response = {
        "interfaces": {"crossfit_aipw": expected_contract}
    }
    provider = AnthropicReplayBackend([core_response, interface_response])
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )

    packet = developer.derive(
        OpenResearchQuestion(
            id="two_phase_theory",
            title="Two-phase theory authoring",
            description="Freeze theory before authoring executable interfaces.",
        )
    )

    assert packet["ok"] is True
    assert validate_theory_packet(packet) == []
    assert len(provider.requests) == 2
    assert [request.model for request in provider.requests] == [
        "claude-haiku-4-5-20251001",
        "claude-haiku-4-5-20251001",
    ]
    assert [
        request.metadata["theory_developer_phase"]
        for request in provider.requests
    ] == ["core_theory_workspace", "estimator_interface_authoring"]
    core_estimator_schema = provider.requests[0].schema["properties"][
        "estimator_specs"
    ]["items"]
    assert {
        "inputs",
        "outputs",
        "normalization",
        "sample_size_order",
    }.issubset(set(core_estimator_schema["required"]))
    interface_schema = provider.requests[1].schema["properties"]["interfaces"]
    assert interface_schema["type"] == "object"
    assert interface_schema["additionalProperties"] is False
    assert interface_schema["required"] == ["crossfit_aipw"]
    assert list(interface_schema["properties"]) == ["crossfit_aipw"]
    contract_schema = interface_schema["properties"]["crossfit_aipw"]
    assert contract_schema["properties"]["request_fields"]["minItems"] == 1
    response_schema = contract_schema["properties"]["response_fields"]
    assert response_schema["minItems"] == response_schema["maxItems"] == 1
    assert contract_schema["properties"]["request_fields"]["items"][
        "properties"
    ]["binding"]["enum"] == list(ESTIMATOR_REQUEST_BINDINGS)
    indexed_rate_schema = response_schema["items"]["properties"][
        "sample_size_rate"
    ]["anyOf"][1]
    assert "polynomial_exponent" in indexed_rate_schema["properties"]
    assert "log_exponent" in indexed_rate_schema["properties"]
    assert {
        "polynomial_exponent",
        "log_exponent",
    }.issubset(indexed_rate_schema["required"])
    estimator = packet["estimator_specs"][0]
    assert estimator["estimator_interface_contract"] == expected_contract
    assert estimator["estimator_interface_contract_id"] == (
        estimator_interface_contract_id(expected_contract)
    )
    assert packet["estimator_interface_authoring"]["n_interfaces"] == 1
    assert packet["estimator_interface_authoring"]["model_tier"] == "haiku"
    assert [row["phase"] for row in packet["theory_generation_phases"]] == [
        "core_theory_workspace",
        "estimator_interface_authoring",
    ]


def test_interface_authoring_cannot_replace_frozen_outputs_with_status_rows() -> None:
    core_response = _sample_response()
    core_estimators = [dict(row) for row in core_response["estimator_specs"]]
    contract = core_estimators[0].pop("estimator_interface_contract")
    core_estimators[0]["outputs"] = [
        "point estimate",
        "estimated standard error",
    ]
    core_response["estimator_specs"] = core_estimators
    provider = SequentialGeneratorBackend(
        [
            core_response,
            {"interfaces": {"crossfit_aipw": contract}},
        ]
    )
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_validation_retries=0,
        ),
    )

    with pytest.raises(PacketValidationError) as exc_info:
        developer.derive(
            OpenResearchQuestion(
                id="frozen_output_count",
                title="Frozen output count",
                description="Keep executable interfaces bound to frozen theory.",
            )
        )

    assert any(
        "response_fields must correspond one-for-one to the 2 frozen outputs"
        in error
        for error in exc_info.value.errors
    )



def test_serious_theory_revision_requires_native_client_tool_backend() -> None:
    parent = _serious_sample_response()
    question = OpenResearchQuestion(
        id="tool_only_revision",
        title="Tool-only theory revision",
        description="Require the model-owned workspace path.",
    )
    context = _metric_theory_revision_context(question=question, parent=parent)
    provider = SequentialGeneratorBackend([])
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            serious_model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            serious_model_tier="haiku",
        ),
    )

    with pytest.raises(
        PacketValidationError,
        match="requires native client-tool turns",
    ):
        developer.derive(question, architect_context=context)

    assert provider.requests == []


def test_theory_revision_uses_model_owned_artifact_workspace() -> None:
    parent = _serious_sample_response()
    question = OpenResearchQuestion(
        id="theory_artifact_workspace",
        title="Theory artifact workspace",
        description="Use one model-owned theory workspace revision.",
    )
    context = _metric_theory_revision_context(question=question, parent=parent)
    revision_inputs = build_theory_developer_revision_inputs(
        context,
        question=question,
    )
    revised_core = json.loads(json.dumps(revision_inputs["base_core_payload"]))
    revised_core["lemma_cards"].append(
        {
            "id": "bounded_outcome_moment_control",
            "statement": "Bounded outcomes imply the required finite moment.",
            "depends_on": ["identify_ate"],
            "used_by": ["aipw_asymptotic_normality"],
            "formalization_difficulty": "medium",
        }
    )
    provider = ScriptedTheoryToolBackend(
        tool_responses=[
            _theory_tool_response(
                ClientToolCall(
                    call_id="read-lemmas",
                    name="read_theory_workspace",
                    input={
                        "artifact_names": [
                            "reviewer_observations",
                            "lemma_cards",
                        ]
                    },
                )
            ),
            _theory_tool_response(
                ClientToolCall(
                    call_id="edit-lemmas",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_theory_artifact_writes(
                        {"lemma_cards": revised_core["lemma_cards"]}
                    ),
                )
            ),
        ],
        generator_responses=[],
    )
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            serious_model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            serious_model_tier="haiku",
            max_validation_retries=0,
        ),
    )

    packet = developer.derive(question, architect_context=context)

    assert packet["ok"] is True
    assert packet["lemma_cards"][-1]["id"] == (
        "bounded_outcome_moment_control"
    )
    assert len(provider.tool_requests) == 2
    assert provider.generator_requests == []
    first_tool_request = provider.tool_requests[0]
    assert first_tool_request.metadata["theory_developer_phase"] == (
        "artifact_workspace_revision"
    )
    assert first_tool_request.metadata["revision_generation_mode"] == (
        "model_owned_artifact_workspace"
    )
    assert {tool.name for tool in first_tool_request.tools} == {
        "read_theory_workspace",
        THEORY_WORKSPACE_WRITE_TOOL,
        THEORY_WORKSPACE_GAP_TOOL,
    }
    first_prompt = str(first_tool_request.messages[0]["content"])
    assert json.dumps(revision_inputs["base_core_payload"]) not in first_prompt
    assert "Authoritative theory workspace catalog" in first_prompt
    assert "First read reviewer_observations by itself" in first_prompt
    assert "critic finding, or next action does not override" in first_prompt
    assert "failed status or nonempty errors is diagnostic only" in first_prompt
    assert revised_core["lemma_cards"][0]["id"] in str(
        provider.tool_requests[1].messages
    )
    assert "The bounded-outcome premise is not explicit." in str(
        provider.tool_requests[1].messages
    )
    transport = packet["theory_revision_transport"]
    assert transport["artifact_kind"] == (
        "TheoryDeveloperWorkspaceRevisionTransport"
    )
    assert transport["revision_mode"] == "model_owned_artifact_workspace"
    assert transport["changed_artifact_names"] == ["lemma_cards"]
    assert transport["model_owned_artifact_edits"] is True
    assert transport["write_transport"] == (
        THEORY_WORKSPACE_DIRECT_WRITE_TRANSPORT
    )
    assert transport["runtime_edited_theory"] is False
    assert "revision_obligations" not in transport
    assert packet["estimator_interface_authoring"]["model_call_used"] is False
    assert packet["theory_generation_phases"][1]["phase"] == (
        "estimator_interface_reuse"
    )
    workspace_evidence = packet["llm_client_tool_loop"]
    assert workspace_evidence["model_owned_theory"] is True
    assert workspace_evidence["runtime_edited_theory"] is False
    assert workspace_evidence["reads"] == 1
    assert workspace_evidence["submissions"] == 1
    assert packet["theory_generation_phases"][0]["phase"] == (
        "artifact_workspace_revision"
    )


def test_default_theory_workspace_budget_allows_observation_recovery() -> None:
    config = ResearchArchitectConfig()

    assert config.theory_workspace_max_turns >= (
        config.theory_workspace_max_reads
        + config.theory_workspace_max_submissions
        + 2
    )


def test_postexecution_theory_revision_uses_current_parent_bound_feedback() -> None:
    parent = _serious_sample_response()
    stale_parent = _serious_sample_response()
    stale_parent["problem_card"] = {
        **stale_parent["problem_card"],
        "estimand": "a stale target that must not be revised",
    }
    question = OpenResearchQuestion(
        id="generic_postexecution_revision",
        title="Generic post-execution theory revision",
        description="Revise the reviewed parent without copying execution outcomes.",
    )
    parent_id = "theory_derivation:current-reviewed-parent"
    material = build_theory_informed_metric_protocol_material(
        theory_packet=parent,
        theory_packet_id=parent_id,
    )
    feedback = {
        "feedback_id": "generated-review-feedback:generic",
        "feedback_type": "generated_code_semantic_review_feedback",
        "repair_scope": "upstream_theory",
        "semantic_review_packet_id": "generated-review:generic",
        "semantic_review_execution_id": "generated-review-execution:generic",
        "findings": [
            {
                "severity": "high",
                "category": "assumption audit",
                "summary": "The parent omits one independently identified premise.",
                "required_change": "Revise the parent semantics and direct dependents.",
                "repair_scope": "upstream_theory",
            }
        ],
        "proof_evidence_status": "NOT_PROOF_EVIDENCE",
    }
    binding = build_theory_developer_revision_binding(
        revision_source="generated_code_semantic_review_postexecution",
        question_id=question.id,
        source_feedback=feedback,
        theory_material=material,
        feedback_id=feedback["feedback_id"],
        upstream_theory_revision_count=2,
        max_upstream_theory_revisions=2,
        execution_results_observed=True,
        source_review_packet_id=feedback["semantic_review_packet_id"],
        source_review_execution_id=feedback["semantic_review_execution_id"],
    )
    context = {
        THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY: binding,
        "environment_feedback": feedback,
        "metric_protocol_prior_theory_material": (
            build_theory_informed_metric_protocol_material(
                theory_packet=stale_parent,
                theory_packet_id="theory_derivation:stale-preflight-parent",
            )
        ),
    }

    feedback["findings"][0]["summary"] = "mutated after binding"
    parent["problem_card"]["estimand"] = "mutated after binding"
    revision_inputs = build_theory_developer_revision_inputs(
        context,
        question=question,
    )

    assert revision_inputs["revision_source"] == (
        "generated_code_semantic_review_postexecution"
    )
    assert revision_inputs["source_theory_packet_id"] == parent_id
    assert revision_inputs["execution_results_observed"] is True
    assert revision_inputs["feedback"]["findings"][0]["summary"] == (
        "The parent omits one independently identified premise."
    )
    assert revision_inputs["base_core_payload"]["problem_card"]["estimand"] == (
        "psi = E[m_1(X)-m_0(X)]"
    )
    assert revision_inputs["parent_estimator_interface_bindings"] == [
        {
            "estimator_id": "crossfit_aipw",
            "core_spec_fingerprint": stable_hash(
                revision_inputs["base_core_payload"]["estimator_specs"][0]
            ),
            "estimator_interface_contract": (
                parent["estimator_specs"][0]["estimator_interface_contract"]
            ),
            "estimator_interface_contract_id": (
                estimator_interface_contract_id(
                    parent["estimator_specs"][0][
                        "estimator_interface_contract"
                    ]
                )
            ),
        }
    ]
    prompt = build_theory_developer_prompt(question, architect_context=context)
    assert "model_owned_theory_artifact_workspace" in prompt
    assert "generated_code_semantic_review_postexecution" in prompt
    assert "theory_derivation:stale-preflight-parent" not in prompt
    prompt_payload = json.loads(prompt.split("\n\n", 1)[1])
    assert prompt_payload["revision_mode"] == (
        "model_owned_theory_artifact_workspace"
    )
    assert "parent_core_packet" not in prompt_payload
    assert "reviewer_feedback" not in prompt_payload
    assert prompt_payload["reviewer_observations"]["workspace_artifact"] == (
        "reviewer_observations"
    )
    assert "write_theory_artifacts" in " ".join(
        prompt_payload["instructions"]
    )

    tampered_context = json.loads(json.dumps(context))
    tampered_context[THEORY_DEVELOPER_REVISION_BINDING_CONTEXT_KEY][
        "source_theory_packet_hash"
    ] = "stale-hash"
    with pytest.raises(PacketValidationError, match="fingerprint does not match"):
        build_theory_developer_revision_inputs(
            tampered_context,
            question=question,
        )


def test_theory_revision_reuses_exact_abi_when_estimator_core_is_unchanged() -> None:
    parent = _serious_sample_response()
    question = OpenResearchQuestion(
        id="targeted_revision_interface_reuse",
        title="Targeted revision interface reuse",
        description="Keep an unchanged model-authored estimator ABI stable.",
    )
    context = _metric_theory_revision_context(question=question, parent=parent)
    revised_problem_card = json.loads(json.dumps(parent["problem_card"]))
    revised_problem_card["assumptions"].append("bounded outcomes")
    provider = ScriptedTheoryToolBackend(
        tool_responses=[
            _theory_tool_response(
                ClientToolCall(
                    call_id="edit-revised-problem-card-for-abi-reuse",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_theory_artifact_writes(
                        {"problem_card": revised_problem_card}
                    ),
                )
            )
        ],
        generator_responses=[],
    )
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            serious_model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            serious_model_tier="haiku",
            max_validation_retries=1,
        ),
    )

    packet = developer.derive(question, architect_context=context)

    assert validate_theory_packet(packet) == []
    assert len(provider.tool_requests) == 1
    assert provider.generator_requests == []
    assert packet["estimator_specs"][0][
        "estimator_interface_contract"
    ] == parent["estimator_specs"][0]["estimator_interface_contract"]
    assert packet["estimator_specs"][0][
        "estimator_interface_contract_id"
    ] == estimator_interface_contract_id(
        parent["estimator_specs"][0]["estimator_interface_contract"]
    )
    assert packet["estimator_interface_authoring"]["artifact_kind"] == (
        "TheoryEstimatorInterfaceReuseRecord"
    )
    assert packet["estimator_interface_authoring"]["model_call_used"] is False
    assert packet["estimator_interface_authoring"]["runtime_edited_interfaces"] is (
        False
    )
    assert [row["phase"] for row in packet["theory_generation_phases"]] == [
        "artifact_workspace_revision",
        "estimator_interface_reuse",
    ]


def test_theory_revision_inputs_do_not_fill_optional_model_content() -> None:
    parent = _serious_sample_response()
    parent_derivation = dict(parent["theory_derivation_packet"])
    parent_derivation.pop("self_critique", None)
    parent_derivation.pop("rejected_alternatives", None)
    parent["theory_derivation_packet"] = parent_derivation
    question = OpenResearchQuestion(
        id="targeted_revision_no_runtime_content_fill",
        title="Targeted revision without runtime content fill",
        description="Preserve the exact parent theory workspace.",
    )
    context = _metric_theory_revision_context(question=question, parent=parent)

    revision_inputs = build_theory_developer_revision_inputs(
        context,
        question=question,
    )

    derivation = revision_inputs["base_core_payload"][
        "theory_derivation_packet"
    ]
    assert "self_critique" not in derivation
    assert "rejected_alternatives" not in derivation


def test_theory_core_validator_enforces_declared_nested_item_shapes() -> None:
    packet = _serious_sample_response()
    packet["simulation_ademp_spec"]["dgps"][0] = {
        "description": "shape drift that must be returned to the model"
    }

    errors = validate_theory_core_packet(packet)

    assert "simulation_ademp_spec.dgps[0] must be a string" in errors


def test_theory_revision_resumes_interface_stage_from_validated_core() -> None:
    parent = _serious_sample_response()
    question = OpenResearchQuestion(
        id="targeted_revision_interface_resume",
        title="Targeted revision interface resume",
        description="Resume only the failed interface stage after core validation.",
    )
    context = _metric_theory_revision_context(question=question, parent=parent)
    revision_inputs = build_theory_developer_revision_inputs(
        context,
        question=question,
    )
    revised_core = json.loads(json.dumps(revision_inputs["base_core_payload"]))
    revised_core["problem_card"]["assumptions"] = [
        *revised_core["problem_card"]["assumptions"],
        "bounded outcomes",
    ]
    revised_core["estimator_specs"][0]["required_assumptions"] = [
        *revised_core["estimator_specs"][0]["required_assumptions"],
        "bounded outcomes",
    ]
    estimator = parent["estimator_specs"][0]
    expected_contract = json.loads(
        json.dumps(estimator["estimator_interface_contract"])
    )
    invalid_contract = json.loads(json.dumps(expected_contract))
    invalid_rate = invalid_contract["response_fields"][0]["sample_size_rate"]
    invalid_rate["contributions"][0]["polynomial_exponent"] = "invalid"
    invalid_interface = {
        "interfaces": {estimator["id"]: invalid_contract}
    }
    still_invalid_interface = json.loads(json.dumps(invalid_interface))
    still_invalid_interface["interfaces"][estimator["id"]]["response_fields"][
        0
    ]["sample_size_rate"]["contributions"][0]["polynomial_exponent"] = (
        "still-invalid"
    )
    first_provider = ScriptedTheoryToolBackend(
        tool_responses=[
            _theory_tool_response(
                ClientToolCall(
                    call_id="edit-revised-problem-card",
                    name=THEORY_WORKSPACE_WRITE_TOOL,
                    input=_theory_artifact_writes(
                        {
                            "problem_card": revised_core["problem_card"],
                            "estimator_specs": revised_core["estimator_specs"],
                        }
                    ),
                )
            )
        ],
        generator_responses=[invalid_interface, still_invalid_interface],
    )
    first_developer = LLMTheoryDeveloperAgent(
        provider=first_provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            serious_model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            serious_model_tier="haiku",
            max_validation_retries=1,
        ),
    )

    with pytest.raises(PacketValidationError) as exc_info:
        first_developer.derive(question, architect_context=context)

    checkpoint = exc_info.value.recovery_checkpoint
    assert checkpoint is not None
    assert checkpoint["completed_phase"] == "artifact_workspace_revision"
    assert checkpoint["failed_phase"] == "estimator_interface_authoring"
    assert checkpoint["kernel_verified"] is False
    assert first_provider.tool_requests[0].metadata[
        "theory_developer_phase"
    ] == "artifact_workspace_revision"
    assert [
        request.metadata["theory_developer_phase"]
        for request in first_provider.generator_requests
    ] == [
        "estimator_interface_authoring",
        "estimator_interface_authoring",
    ]
    assert first_provider.generator_requests[1].metadata[
        "structured_output_retry_mode"
    ] == (
        "full_packet_regeneration"
    )
    assert "allowed_semantic_reference_ids" in (
        first_provider.generator_requests[1].user_prompt
    )
    assert "orthogonal_expansion" in (
        first_provider.generator_requests[1].user_prompt
    )
    repair_payload = json.loads(
        first_provider.generator_requests[1].user_prompt.split("\n\n", 1)[1]
    )
    repair_errors = repair_payload["local_validation_errors"]
    assert any(
        f'interfaces["{estimator["id"]}"]' in error
        for error in repair_errors
    )
    assert all("interfaces[0]" not in error for error in repair_errors)
    assert "subsystem_repair_context" not in repair_payload
    original_interface_payload = json.loads(
        repair_payload["original_request"].split("\n\n", 1)[1]
    )
    assert original_interface_payload["frozen_core_theory"]["problem_card"] == {
        field: revised_core["problem_card"][field]
        for field in (
            "observed_data",
            "dgp",
            "estimand",
            "assumptions",
            "asymptotic_regime",
        )
    }
    assert json.loads(repair_payload["previous_candidate"]) == (
        invalid_interface
    )

    retry_context = dict(context)
    retry_context["theory_developer_source_environment_feedback"] = dict(
        context["environment_feedback"]
    )
    retry_context["environment_feedback"] = {
        "artifact_kind": "RuntimeTheoryDeveloperValidationFeedback",
        "truncation_detected": False,
        "recovery_checkpoint": checkpoint,
    }
    valid_interface = {
        "interfaces": {estimator["id"]: expected_contract}
    }
    retry_provider = SequentialGeneratorBackend([valid_interface])
    retry_developer = LLMTheoryDeveloperAgent(
        provider=retry_provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            serious_model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            serious_model_tier="haiku",
            max_validation_retries=1,
        ),
    )

    packet = retry_developer.derive(question, architect_context=retry_context)

    assert validate_theory_packet(packet) == []
    assert len(retry_provider.requests) == 1
    assert retry_provider.requests[0].metadata["theory_developer_phase"] == (
        "estimator_interface_authoring"
    )
    assert packet["theory_generation_phases"][0]["phase"] == (
        "artifact_workspace_revision"
    )
    assert packet["theory_revision_transport"]["feedback_id"] == (
        context["environment_feedback"]["feedback_id"]
    )


def test_theory_revision_rejects_lineage_mismatch_before_provider_call() -> None:
    parent = _serious_sample_response()
    question = OpenResearchQuestion(
        id="targeted_revision_mismatch",
        title="Targeted revision lineage",
        description="Reject feedback for different parent bytes.",
    )
    context = _metric_theory_revision_context(
        question=question,
        parent=parent,
    )
    feedback = dict(context["environment_feedback"])
    feedback["source_theory_packet_hash"] = "wrong-parent-hash"
    context["environment_feedback"] = feedback
    provider = SequentialGeneratorBackend([])
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="anthropic",
            model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            model_tier="haiku",
            serious_model=DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            serious_model_tier="haiku",
        ),
    )

    with pytest.raises(PacketValidationError, match="packet hashes must match"):
        developer.derive(question, architect_context=context)

    assert provider.requests == []


def test_theory_developer_uses_shared_full_packet_regeneration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def capture_validated_packet(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(
        "ai_statistician.research_architect.generate_validated_json_packet",
        capture_validated_packet,
    )
    developer = LLMTheoryDeveloperAgent(
        provider=SequentialGeneratorBackend([]),
        config=ResearchArchitectConfig(
            provider_name="sequential_test",
            model="claude-haiku-4-5-20251001",
            model_tier="haiku",
            max_validation_retries=2,
        ),
    )

    packet = developer.derive(
        OpenResearchQuestion(
            id="strict_progress_patch",
            title="Full packet regeneration",
            description="Exercise the shared TheoryDeveloper retry policy.",
        )
    )

    assert packet == {"ok": True}
    assert "semantic_patch_repair" not in captured
    assert "allow_progress_repair_extension" not in captured
    assert "repair_context_builder" not in captured
    assert "retry_prompt_builder" not in captured
    assert captured["max_validation_retries"] == 2


def test_theory_developer_truncation_recovery_is_serious_and_bounded() -> None:
    provider = SequentialGeneratorBackend(
        [
            '{"problem_card":{"observed_data":"truncated"',
            '{"problem_card":{"observed_data":"still truncated"',
        ]
    )
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="sequential_test",
            model="repair-test-model",
            max_validation_retries=2,
        ),
    )
    context = {
        "architect_runtime_plan": {
            "evidence_contract": {"evaluation_mode": "capability_eval"}
        },
        "environment_feedback": {
            "artifact_kind": "RuntimeTheoryDeveloperValidationFeedback",
            "failure_classification": "theory_developer_packet_truncated_json",
            "truncation_detected": True,
            "required_revision": "Return a complete serious-theory handoff.",
        },
    }

    with pytest.raises(PacketValidationError):
        developer.derive(
            OpenResearchQuestion(
                id="transport_recovery",
                title="Transport recovery",
                description="Recover a serious theory packet after truncation.",
            ),
            architect_context=context,
        )

    assert len(provider.requests) == 2
    request = provider.requests[0]
    assert request.metadata["transport_recovery"] is True
    assert request.metadata["effective_max_validation_retries"] == 1
    derivation_schema = request.schema["properties"][
        "theory_derivation_packet"
    ]["properties"]
    assert derivation_schema["derivation_steps"]["minItems"] == 1
    assert derivation_schema["derivation_steps"]["maxItems"] == 5
    assert derivation_schema["equation_chain"]["minItems"] == 1
    assert derivation_schema["equation_chain"]["maxItems"] == 4
    assert derivation_schema["sanity_checks"]["minItems"] == 1
    assert derivation_schema["sanity_checks"]["maxItems"] == 3
    assert request.schema["properties"]["problem_card"]["properties"][
        "observed_data"
    ]["maxLength"] == 320
    assert '"transport_recovery":true' in request.user_prompt


def test_llm_theory_developer_repairs_invalid_json_packet_before_accepting() -> None:
    oversized_bad_response = {"problem_card": {"observed_data": "x" * 4000}}
    provider = SequentialGeneratorBackend(
        [
            oversized_bad_response,
            _sample_response(),
        ]
    )
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="sequential_test",
            model="repair-test-model",
            max_validation_retries=1,
        ),
    )

    packet = developer.derive(
        OpenResearchQuestion(
            id="repair",
            title="Repair packet",
            description="Force a malformed first LLM packet, then repair it.",
            tags=("repair",),
        )
    )

    assert packet["ok"] is True
    assert packet["structured_output_retry_attempts"] == 1
    assert len(packet["structured_output_retry_history"]) == 2
    assert packet["structured_output_retry_history"][0]["ok"] is False
    assert "missing or empty field" in " ".join(packet["structured_output_retry_history"][0]["errors"])
    assert packet["structured_output_retry_history"][1]["ok"] is True
    assert len(provider.requests) == 2
    assert provider.requests[1].metadata["structured_output_retry_attempt"] == 1
    assert "Your previous response failed AI Statistician local validation" in provider.requests[1].user_prompt
    assert "required_output_contract" in provider.requests[1].user_prompt
    assert "Rewrite the full JSON object from scratch" in provider.requests[1].user_prompt
    assert provider.requests[1].user_prompt.count("x") >= 4000


def test_llm_theory_developer_default_repair_budget_allows_two_repairs() -> None:
    provider = SequentialGeneratorBackend(
        [
            '{"problem_card": {"observed_data": "broken"',
            {"problem_card": {"observed_data": "still missing required fields"}},
            _sample_response(),
        ]
    )
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(
            provider_name="sequential_test",
            model="repair-test-model",
        ),
    )

    packet = developer.derive(
        OpenResearchQuestion(
            id="repair_budget",
            title="Repair budget",
            description="Allow two compact repairs before failing.",
            tags=("repair",),
        )
    )

    assert packet["ok"] is True
    assert packet["structured_output_retry_attempts"] == 2
    assert len(packet["structured_output_retry_history"]) == 3
    assert [row["ok"] for row in packet["structured_output_retry_history"]] == [
        False,
        False,
        True,
    ]
    assert len(provider.requests) == 3
    assert provider.requests[1].metadata["structured_output_retry_max_attempts"] == 2
    assert provider.requests[2].metadata["structured_output_retry_attempt"] == 2
    assert all(
        row["response_text_chars"] > 0
        for row in packet["structured_output_retry_history"]
    )
    assert all(
        row["response_metadata"]["provider_stop_reason"] == "end_turn"
        for row in packet["structured_output_retry_history"]
    )


def test_llm_theory_developer_canonicalizes_common_schema_variants() -> None:
    response = _sample_response()
    derivation = dict(response["theory_derivation_packet"])
    derivation["derivation_steps"] = [
        {
            "step_id": "D1",
            "statement": "Exchangeability makes the test rank uniform.",
            "argument": "Permutation symmetry over calibration plus test scores.",
        },
        {
            "step_id": "D2",
            "statement": "The conformal quantile keeps all but alpha ranks.",
            "argument": "Use ceil((n+1)(1-alpha)) rank cutoff.",
        },
        {
            "step_id": "D3",
            "statement": "Coverage follows from the retained rank fraction.",
            "argument": "The retained fraction is at least 1-alpha.",
        },
    ]
    derivation["equation_chain"] = [
        {
            "id": "E1",
            "left": "P(covered)",
            "relation": ">=",
            "right": "ceil((n+1)(1-alpha))/(n+1)",
            "reason": "rank uniformity",
        },
        {
            "id": "E2",
            "left": "ceil((n+1)(1-alpha))/(n+1)",
            "relation": ">=",
            "right": "1-alpha",
            "reason": "ceiling arithmetic",
        },
    ]
    derivation["assumption_ledger"] = [
        {"name": "exchangeable scores", "role": "identification"},
        {"condition": "fixed alpha in (0,1)", "role": "regularity"},
    ]
    derivation.pop("formalization_handoff", None)
    response["theory_derivation_packet"] = derivation
    estimator = dict(response["estimator_specs"][0])
    interface = dict(estimator["estimator_interface_contract"])
    response_fields = [dict(row) for row in interface["response_fields"]]
    response_fields[0]["derivation_ref"] = "E2"
    rate = dict(response_fields[0]["sample_size_rate"])
    contributions = [dict(row) for row in rate["contributions"]]
    contributions[0]["justification_ref"] = "E2"
    rate["contributions"] = contributions
    response_fields[0]["sample_size_rate"] = rate
    interface["response_fields"] = response_fields
    estimator["estimator_interface_contract"] = interface
    response["estimator_specs"] = [estimator]
    provider = SequentialGeneratorBackend([response])
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(provider_name="sequential_test"),
    )

    packet = developer.derive(
        OpenResearchQuestion(
            id="canonicalize",
            title="Canonicalize packet",
            description="Accept common field variants without dropping boundaries.",
            tags=("runtime",),
        )
    )

    theory = packet["theory_derivation_packet"]
    assert packet["ok"] is True
    assert theory["derivation_steps"][0]["claim"] == (
        "Exchangeability makes the test rank uniform."
    )
    assert theory["derivation_steps"][0]["equation_or_argument"] == (
        "Permutation symmetry over calibration plus test scores."
    )
    assert theory["equation_chain"][0]["lhs"] == "P(covered)"
    assert theory["equation_chain"][0]["justification"] == "rank uniformity"
    assert theory["assumption_ledger"][0]["assumption"] == "exchangeable scores"
    assert theory["assumption_ledger"][0]["used_in_inferred_by_runtime"] is True
    assert theory["formalization_handoff"][
        "runtime_inferred_from_formalization_requests"
    ] is True
    assert packet["theory_derivation_contract"]["has_formalization_handoff"] is True
    assert packet["proof_evidence_status"] == THEORY_DERIVATION_NOT_PROOF_EVIDENCE


def test_llm_theory_developer_resolves_model_tier_at_request_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "claude-sonnet-policy-test",
    )
    provider = SequentialGeneratorBackend([_sample_response()])
    developer = LLMTheoryDeveloperAgent(
        provider=provider,
        config=ResearchArchitectConfig(provider_name="anthropic"),
    )

    packet = developer.derive(
        OpenResearchQuestion(
            id="tier_policy",
            title="Tier policy",
            description="Check dynamic Claude tier resolution.",
            tags=("runtime",),
        )
    )

    request = provider.requests[0]
    assert request.model == "claude-sonnet-policy-test"
    assert request.metadata["provider_name"] == "anthropic"
    assert request.metadata["model_tier"] == "sonnet"
    assert request.metadata["resolved_model"] == "claude-sonnet-policy-test"
    assert packet["provider"] == "anthropic"
    assert packet["model"] == "claude-sonnet-policy-test"
    assert packet["model_tier"] == "sonnet"


def test_generator_theory_proposer_resolves_haiku_tier_at_request_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        "claude-haiku-policy-test",
    )
    provider = SequentialGeneratorBackend(
        [
            {
                "dgp_family": "normal",
                "estimator_family": "sample_mean",
                "true_params": {"mean": 0.0, "variance": 1.0},
                "tags": ["mean"],
                "confidence": 0.8,
                "rationale": "normal sample mean",
            }
        ]
    )
    proposer = GeneratorTheoryProposer(
        provider=provider,
        provider_name="anthropic",
    )

    proposal = proposer.propose({"question": "estimate a normal mean"})

    request = provider.requests[0]
    assert request.model == "claude-haiku-policy-test"
    assert request.metadata["provider_name"] == "anthropic"
    assert request.metadata["model_tier"] == "haiku"
    assert request.metadata["resolved_model"] == "claude-haiku-policy-test"
    assert proposal.source == "anthropic:claude-haiku-policy-test"
    assert proposal.dgp_family == "normal"
    assert proposal.estimator_family == "sample_mean"


def test_generator_theory_proposer_requires_provider_identity() -> None:
    proposer = GeneratorTheoryProposer(provider=ProviderWithoutIdentity())

    with pytest.raises(ValueError, match="requires an explicit provider_name"):
        proposer.propose({"question": "estimate a normal mean"})


def test_generator_theory_proposer_rejects_codex_provider_alias() -> None:
    provider = SequentialGeneratorBackend(
        [
            {
                "dgp_family": "normal",
                "estimator_family": "sample_mean",
                "true_params": {"mean": 0.0, "variance": 1.0},
            }
        ]
    )
    proposer = GeneratorTheoryProposer(
        provider=provider,
        provider_name="codex_exec",
    )

    with pytest.raises(ValueError, match="Codex/Codex exec are not accepted"):
        proposer.propose({"question": "estimate a normal mean"})

    assert provider.requests == []


def test_research_architect_cli_static_provider_exports_artifacts() -> None:
    root = Path("runs/test_research_architect_cli")
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    question_file = root / "questions.json"
    response_file = root / "response.json"
    out_dir = root / "out"
    question_file.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "q_cli",
                        "title": "CLI theory task",
                        "description": "Find a robust estimator and theorem.",
                        "tags": ["robust"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    response_file.write_text(json.dumps(_sample_response()), encoding="utf-8")

    code = main(
        [
            "research-architect-theory",
            "--provider",
            "static",
            "--static-response-file",
            str(response_file),
            "--question-file",
            str(question_file),
            "--out",
            str(out_dir),
        ]
    )

    assert code == 0
    manifest = json.loads((out_dir / "research_architect_manifest.json").read_text())
    assert manifest["n_questions"] == 1
    assert manifest["all_packets_ok"]
    assert Path(manifest["artifacts"]["evidence_ledger"]).exists()


def test_research_architect_cli_binds_explicit_haiku_to_serious_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class NoCallBackend:
        provider_name = "anthropic"

    captured: dict[str, object] = {}

    monkeypatch.setattr(
        cli_module,
        "_build_theory_generator_backend",
        lambda **_kwargs: (NoCallBackend(), "anthropic"),
    )

    def fake_run(the_architect, questions, *, architect_context):
        captured["config"] = the_architect.theory_developer.config
        return {
            "n_questions": len(questions),
            "n_theory_derivation_packets": len(questions),
            "all_packets_ok": True,
            "proof_evidence_status": THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
        }

    monkeypatch.setattr(
        cli_module.ResearchArchitectAgent,
        "run_theory_development",
        fake_run,
    )

    code = main(
        [
            "research-architect-theory",
            "--question-file",
            "examples/research_questions.json",
            "--question-id",
            "sequential_anytime_bernoulli",
            "--provider",
            "anthropic",
            "--llm-model",
            DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL,
            "--max-tokens",
            "8000",
            "--out",
            str(tmp_path),
        ]
    )

    assert code == 0
    config = captured["config"]
    assert config.model == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
    assert config.model_tier == "haiku"
    assert config.serious_model == DEFAULT_CLAUDE_HAIKU_GENERATOR_MODEL
    assert config.serious_model_tier == "haiku"
    assert config.serious_max_tokens == 8000


def test_live_llm_cli_defaults_to_anthropic_cost_aware_models(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "AI_STATISTICIAN_LLM_PROVIDER",
        "AI_STATISTICIAN_LLM_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_MODEL",
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL",
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_SONNET_MODEL",
        "AI_STATISTICIAN_CLAUDE_OPUS_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_OPUS_MODEL",
        "AI_STATISTICIAN_THEORY_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)

    parser = build_parser()
    architect_args = parser.parse_args(["research-architect-theory"])
    runtime_args = parser.parse_args(["research-agent-runtime"])
    intake_args = parser.parse_args(["theory-intake", "--question-file", "examples/questions.json"])

    assert architect_args.provider == "anthropic"
    assert architect_args.llm_model == ""
    assert default_generator_model(
        architect_args.provider,
        architect_args.llm_model,
        model_tier="sonnet",
    ) == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    assert runtime_args.provider == "anthropic"
    assert runtime_args.architect_coordinator_provider == "same"
    assert runtime_args.generated_code_semantic_reviewer_provider == "none"
    assert runtime_args.formal_target_semantic_reviewer_provider == "none"
    assert runtime_args.llm_model == ""
    assert runtime_args.theory_model_tier == "sonnet"
    assert runtime_args.serious_theory_llm_model == ""
    assert runtime_args.serious_theory_model_tier == "sonnet"
    assert runtime_args.serious_theory_max_tokens == 10000
    assert default_generator_model(
        runtime_args.provider,
        runtime_args.llm_model,
        model_tier="sonnet",
    ) == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    assert default_generator_model(
        runtime_args.provider,
        runtime_args.serious_theory_llm_model,
        model_tier=runtime_args.serious_theory_model_tier,
    ) == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    assert intake_args.llm_provider == "anthropic"
    assert intake_args.llm_model == ""
    assert default_generator_model(
        intake_args.llm_provider,
        intake_args.llm_model,
        model_tier="haiku",
    ) == "claude-haiku-4-5-20251001"
    runtime_default_model = default_generator_model(runtime_args.provider, model_tier="sonnet")
    preflight_source_retriever = object()
    architect = _build_architect_coordinator_agent_from_args(
        runtime_args,
        default_model=runtime_default_model,
        formal_source_retriever=preflight_source_retriever,
    )
    assert architect.config.model == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    assert architect.metric_semantic_reviewer.source_retriever is (
        preflight_source_retriever
    )
    algorithm_engineer = _build_algorithm_engineer_agent_from_args(
        runtime_args,
        default_model=runtime_default_model,
    )
    assert algorithm_engineer.config.model == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    assert algorithm_engineer.config.max_validation_retries == 0
    assert (
        _build_formalizer_agent_from_args(
            runtime_args,
            default_model=runtime_default_model,
        ).config.model
        == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    )
    simulation_engineer = _build_simulation_engineer_agent_from_args(
        runtime_args,
        default_model=runtime_default_model,
    )
    assert simulation_engineer.config.model == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    assert simulation_engineer.config.max_validation_retries == 0
    assert (
        _build_critic_evaluator_agent_from_args(
            runtime_args,
            default_model=runtime_default_model,
        ).config.model
        == "claude-haiku-4-5-20251001"
    )
    runtime_args.generated_code_semantic_reviewer_provider = "same"
    semantic_reviewer = _build_generated_code_semantic_reviewer_agent_from_args(
        runtime_args,
        default_model=runtime_default_model,
    )
    assert semantic_reviewer is not None
    assert semantic_reviewer.config.model == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    assert semantic_reviewer.config.model_tier == "sonnet"
    runtime_args.formal_target_semantic_reviewer_provider = "same"
    formal_target_reviewer = (
        _build_formal_target_semantic_reviewer_agent_from_args(
            runtime_args,
            default_model=runtime_default_model,
        )
    )
    assert formal_target_reviewer is not None
    assert formal_target_reviewer.config.model == DEFAULT_CLAUDE_SONNET_GENERATOR_MODEL
    assert formal_target_reviewer.config.model_tier == "sonnet"


def test_live_evaluation_builders_are_pinned_to_current_haiku(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in (
        "AI_STATISTICIAN_LLM_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_MODEL",
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL",
        "AI_STATISTICIAN_THEORY_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)
    args = build_parser().parse_args(
        ["research-agent-runtime", "--capability-eval"]
    )
    args.generated_code_semantic_reviewer_provider = "same"
    args.formal_target_semantic_reviewer_provider = "same"
    args.llm_model = "claude-sonnet-4-6"
    args.serious_theory_llm_model = "claude-sonnet-4-6"
    args.architect_llm_model = "claude-sonnet-4-6"
    args.algorithm_llm_model = "claude-sonnet-4-6"
    args.simulation_llm_model = "claude-sonnet-4-6"
    args.formalizer_llm_model = "claude-sonnet-4-6"

    _apply_research_agent_runtime_evaluation_model_policy(args)

    expected_model = "claude-haiku-4-5-20251001"
    assert args.evaluation_claude_model_tier == "haiku"
    assert args.evaluation_claude_model == expected_model
    assert args.theory_model_tier == "haiku"
    assert args.serious_theory_model_tier == "haiku"
    default_model = default_generator_model(
        args.provider,
        model_tier=args.evaluation_claude_model_tier,
    )
    agents = (
        _build_architect_coordinator_agent_from_args(
            args,
            default_model=default_model,
        ),
        _build_algorithm_engineer_agent_from_args(
            args,
            default_model=default_model,
        ),
        _build_simulation_engineer_agent_from_args(
            args,
            default_model=default_model,
        ),
        _build_formalizer_agent_from_args(
            args,
            default_model=default_model,
        ),
        _build_critic_evaluator_agent_from_args(
            args,
            default_model=default_model,
        ),
        _build_generated_code_semantic_reviewer_agent_from_args(
            args,
            default_model=default_model,
        ),
        _build_formal_target_semantic_reviewer_agent_from_args(
            args,
            default_model=default_model,
        ),
    )
    assert all(agent is not None for agent in agents)
    assert all(agent.config.model_tier == "haiku" for agent in agents)
    assert all(agent.config.model == expected_model for agent in agents)
    assert agents[1].config.max_validation_retries == 0
    assert agents[2].config.max_validation_retries == 0
    assert agents[5].config.max_validation_retries == 2
    architect = agents[0]
    assert architect.metric_semantic_reviewer.config.model_tier == "haiku"


def test_cli_never_offers_opus_as_a_live_model_tier() -> None:
    pending = [("root", build_parser())]
    seen: set[int] = set()
    offenders: list[str] = []

    while pending:
        command_path, parser = pending.pop()
        if id(parser) in seen:
            continue
        seen.add(id(parser))
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                pending.extend(
                    (f"{command_path}/{name}", subparser)
                    for name, subparser in action.choices.items()
                )
                continue
            choices = getattr(action, "choices", None)
            if choices and "opus" in {str(value).lower() for value in choices}:
                offenders.append(f"{command_path}:{action.dest}:choices")
            default = getattr(action, "default", None)
            if isinstance(default, str) and default.lower() == "opus":
                offenders.append(f"{command_path}:{action.dest}:default")

    assert offenders == []


def test_live_llm_backend_rejects_codex_provider_for_main_cli() -> None:
    with pytest.raises(ValueError, match="unknown theory provider: codex"):
        _build_theory_generator_backend(provider_name="codex")



def test_theory_prompt_uses_current_sources_without_historical_routing_memory() -> None:
    prompt = build_theory_developer_prompt(
        OpenResearchQuestion(
            id="generic_prompt_compaction",
            title="Prompt compaction",
            description="Use current task evidence without historical route recipes.",
            tags=("statistics",),
        ),
        architect_context={
            "runtime_task": {
                "task_id": "theory:current",
                "owner_subsystem": "TheoryDeveloper",
                "objective": "derive the current theory",
                "inputs": {"large_private_payload": "do not include"},
            },
            "retrieval_context": {
                "formal_source_hits": [
                    {
                        "theorem_goal_id": "current_goal",
                        "hits": [
                            {
                                "source_id": "statlib",
                                "path": "Statlib/Current.lean",
                                "name": "Statlib.current_bound",
                                "signature": "theorem current_bound (h : P) : Q",
                                "declaration_doc": "Current task declaration.",
                            }
                        ],
                    }
                ],
                "boundary": "Retrieval hits are not proof evidence.",
            },
            "environment_feedback": {
                "feedback_source": "CriticEvaluator",
                "formal_subclaim_feedback": [
                    {
                        "id": "current_gap",
                        "status": "FORMAL_GAP",
                        "gap_reason": "current task assumption is unresolved",
                    }
                ],
            },
            "runtime_learning_memory": {
                "rows": [
                    {
                        "question_id": "historical_task_must_not_leak",
                        "target_behavior": "historical routing recipe",
                    }
                ]
            },
        },
    )

    assert "Statlib.current_bound" in prompt
    assert "theorem current_bound (h : P) : Q" in prompt
    assert "current task assumption is unresolved" in prompt
    assert "Retrieval hits are not proof evidence" in prompt
    assert "historical_task_must_not_leak" not in prompt
    assert "historical routing recipe" not in prompt
    assert "large_private_payload" not in prompt



def test_llm_theory_developer_rejects_kernel_verified_claims() -> None:
    bad = _sample_response()
    bad["formalization_requests"] = [
        {
            "id": "bad_verified_claim",
            "target_theorem_card": "aipw_asymptotic_normality",
            "lean_statement_sketch": "theorem bad ...",
            "semantic_alignment_constraints": ["none"],
            "kernel_status": "KERNEL_VERIFIED",
        }
    ]
    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(bad),
        config=ResearchArchitectConfig(provider_name="static", model="static-theory-model"),
    )

    with pytest.raises(ValueError, match="forbidden proof status"):
        developer.derive(
            OpenResearchQuestion(
                id="bad",
                title="Bad proof claim",
                description="Should reject proof overclaiming.",
            )
        )


def _research_report(
    *,
    question,
    problem,
    procedures,
    theorem_goals,
    simulation,
    agenda_item,
    status,
):
    from ai_statistician.research_schema import ResearchReport

    return ResearchReport(
        question=question,
        problem=problem,
        procedures=procedures,
        knowledge=[],
        paper_sources=[],
        formal_subclaims=[],
        simulations=[simulation],
        theorem_goals=theorem_goals,
        theory_plan={"next_iteration_agenda": {"items": [agenda_item]}},
        status=status,
    )
