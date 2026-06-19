from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

import pytest

from ai_statistician.cli import (
    _build_algorithm_engineer_agent_from_args,
    _build_architect_coordinator_agent_from_args,
    _build_critic_evaluator_agent_from_args,
    _build_formalizer_agent_from_args,
    _build_simulation_engineer_agent_from_args,
    _build_theory_generator_backend,
    build_parser,
    main,
)
from ai_statistician.model_backend import GeneratorRequest, GeneratorResponse, default_generator_model
from ai_statistician.research_architect import (
    KERNEL_PROOF_BOUNDARY,
    LLMTheoryDeveloperAgent,
    LLMTheoryDeveloperRepairHandler,
    ResearchArchitectAgent,
    ResearchArchitectConfig,
    StaticArchitectLLMProvider,
    THEORY_DERIVATION_NOT_PROOF_EVIDENCE,
    build_theory_developer_prompt,
)
from ai_statistician.research_lab import (
    ProblemFormalizer,
    ResearchSimulator,
    TheoryPlanner,
    load_open_research_questions,
)
from ai_statistician.research_loop import ResearchLoopCoordinator
from ai_statistician.research_schema import OpenResearchQuestion
from ai_statistician.theory_proposal import GeneratorTheoryProposer


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
                    "id": "orthogonal_score",
                    "claim": "AIPW score has first-order insensitivity to nuisance error.",
                    "equation_or_argument": "phi = m1-m0 + A/e(Y-m1) - (1-A)/(1-e)(Y-m0) - psi",
                    "depends_on": ["identification"],
                    "risk": "positivity and integrability are required",
                }
            ],
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
                "tuning": ["number of folds"],
                "required_assumptions": ["positivity", "product-rate nuisance convergence"],
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
    assert packet["kernel_verified"] is False
    assert ledger["evidence_status"] == "PROPOSAL_RECORDED_REQUIRES_GATES"
    assert ledger["boundary"] == KERNEL_PROOF_BOUNDARY


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
            max_repair_attempts=1,
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
    assert packet["llm_json_repair_attempts"] == 1
    assert len(packet["llm_json_repair_history"]) == 2
    assert packet["llm_json_repair_history"][0]["ok"] is False
    assert "missing or empty field" in " ".join(packet["llm_json_repair_history"][0]["errors"])
    assert packet["llm_json_repair_history"][1]["ok"] is True
    assert len(provider.requests) == 2
    assert provider.requests[1].metadata["json_repair_attempt"] == 1
    assert "Your previous response failed AI Statistician local validation" in provider.requests[1].user_prompt
    assert "required_output_contract" in provider.requests[1].user_prompt
    assert "Keep all fields concise" in provider.requests[1].user_prompt
    assert provider.requests[1].user_prompt.count("x") < 2500


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
    assert packet["llm_json_repair_attempts"] == 2
    assert len(packet["llm_json_repair_history"]) == 3
    assert [row["ok"] for row in packet["llm_json_repair_history"]] == [
        False,
        False,
        True,
    ]
    assert len(provider.requests) == 3
    assert provider.requests[1].metadata["json_repair_max_attempts"] == 2
    assert provider.requests[2].metadata["json_repair_attempt"] == 2
    assert all(
        row["response_text_chars"] > 0
        for row in packet["llm_json_repair_history"]
    )
    assert all(
        row["response_metadata"]["provider_stop_reason"] == "end_turn"
        for row in packet["llm_json_repair_history"]
    )


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


@pytest.mark.parametrize("provider_name", ("codex_exec", "claude_code"))
def test_generator_theory_proposer_rejects_agent_provider_alias(
    provider_name: str,
) -> None:
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
        provider_name=provider_name,
    )

    with pytest.raises(ValueError, match="Agent-style CLI providers"):
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


def test_live_llm_cli_defaults_to_anthropic_cost_aware_models(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "AI_STATISTICIAN_LLM_PROVIDER",
        "AI_STATISTICIAN_LLM_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_MODEL",
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL",
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_SONNET_MODEL",
        "AI_STATISTICIAN_THEORY_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)

    parser = build_parser()
    architect_args = parser.parse_args(["research-architect-theory"])
    runtime_args = parser.parse_args(["research-agent-runtime"])
    loop_args = parser.parse_args(["research-loop"])
    intake_args = parser.parse_args(["theory-intake", "--question-file", "examples/questions.json"])

    assert architect_args.provider == "anthropic"
    assert architect_args.llm_model == ""
    assert default_generator_model(
        architect_args.provider,
        architect_args.llm_model,
        model_tier="sonnet",
    ) == "claude-sonnet-4-6"
    assert runtime_args.provider == "anthropic"
    assert runtime_args.architect_coordinator_provider == "same"
    assert runtime_args.llm_model == ""
    assert default_generator_model(
        runtime_args.provider,
        runtime_args.llm_model,
        model_tier="sonnet",
    ) == "claude-sonnet-4-6"
    assert loop_args.llm_theory_provider == "anthropic"
    assert loop_args.llm_theory_model == ""
    assert default_generator_model(
        loop_args.llm_theory_provider,
        loop_args.llm_theory_model,
        model_tier="sonnet",
    ) == "claude-sonnet-4-6"
    assert intake_args.llm_provider == "anthropic"
    assert intake_args.llm_model == ""
    assert default_generator_model(
        intake_args.llm_provider,
        intake_args.llm_model,
        model_tier="haiku",
    ) == "claude-haiku-4-5-20251001"
    runtime_default_model = default_generator_model(runtime_args.provider, model_tier="sonnet")
    assert _build_architect_coordinator_agent_from_args(runtime_args, default_model=runtime_default_model).config.model == "claude-sonnet-4-6"
    assert _build_algorithm_engineer_agent_from_args(runtime_args, default_model=runtime_default_model).config.model == "claude-haiku-4-5-20251001"
    assert _build_formalizer_agent_from_args(runtime_args, default_model=runtime_default_model).config.model == "claude-sonnet-4-6"
    assert _build_simulation_engineer_agent_from_args(runtime_args, default_model=runtime_default_model).config.model == "claude-haiku-4-5-20251001"
    assert _build_critic_evaluator_agent_from_args(runtime_args, default_model=runtime_default_model).config.model == "claude-haiku-4-5-20251001"


def test_runtime_llm_model_override_does_not_collapse_haiku_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in (
        "AI_STATISTICIAN_LLM_PROVIDER",
        "AI_STATISTICIAN_LLM_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_MODEL",
        "AI_STATISTICIAN_CLAUDE_HAIKU_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_HAIKU_MODEL",
        "AI_STATISTICIAN_CLAUDE_SONNET_MODEL",
        "AI_STATISTICIAN_ANTHROPIC_SONNET_MODEL",
        "AI_STATISTICIAN_THEORY_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)

    parser = build_parser()
    runtime_args = parser.parse_args(
        ["research-agent-runtime", "--llm-model", "claude-sonnet-4-6"]
    )

    runtime_default_model = default_generator_model(
        runtime_args.provider,
        runtime_args.llm_model,
        model_tier="sonnet",
    )

    assert runtime_default_model == "claude-sonnet-4-6"
    assert (
        _build_architect_coordinator_agent_from_args(
            runtime_args,
            default_model=runtime_default_model,
        ).config.model
        == "claude-sonnet-4-6"
    )
    assert (
        _build_formalizer_agent_from_args(
            runtime_args,
            default_model=runtime_default_model,
        ).config.model
        == "claude-sonnet-4-6"
    )
    assert (
        _build_algorithm_engineer_agent_from_args(
            runtime_args,
            default_model=runtime_default_model,
        ).config.model
        == "claude-haiku-4-5-20251001"
    )
    assert (
        _build_simulation_engineer_agent_from_args(
            runtime_args,
            default_model=runtime_default_model,
        ).config.model
        == "claude-haiku-4-5-20251001"
    )
    assert (
        _build_critic_evaluator_agent_from_args(
            runtime_args,
            default_model=runtime_default_model,
        ).config.model
        == "claude-haiku-4-5-20251001"
    )


def test_live_llm_backend_rejects_codex_provider_for_main_cli() -> None:
    with pytest.raises(ValueError, match="unknown theory provider: codex"):
        _build_theory_generator_backend(provider_name="codex")


def test_theory_developer_prompt_compacts_runtime_retrieval_context() -> None:
    long_signature = "theorem very_long " + ("x " * 600)
    prompt = build_theory_developer_prompt(
        OpenResearchQuestion(
            id="conformal_prompt_compaction",
            title="Prompt compaction",
            description="Check bounded retrieval context.",
            tags=("conformal",),
        ),
        architect_context={
            "runtime_task": {
                "task_id": "theory:test",
                "owner_subsystem": "TheoryDeveloper",
                "objective": "derive theory",
                "inputs": {"large": "do not include"},
            },
            "retrieval_context": {
                "knowledge_cards": [
                    {
                        "id": "split_conformal",
                        "title": "Split conformal",
                        "source_type": "method",
                        "summary": "coverage " * 100,
                        "tags": ["conformal", "coverage"],
                    }
                ],
                "paper_sources": [],
                "formal_source_hits": [
                    {
                        "theorem_goal_id": "coverage",
                        "hits": [
                            {
                                "source_id": "mathlib",
                                "path": "Mathlib/Probability.lean",
                                "line": 10,
                                "kind": "theorem",
                                "name": "Probability.coverage",
                                "signature": long_signature,
                                "matched_terms": ["probability"],
                            }
                        ],
                    }
                ],
                "boundary": "Retrieval hits are not proof evidence.",
            },
            "environment_feedback": {
                "feedback_source": "CriticEvaluator",
                "critic_repair_round": 0,
                "next_critic_repair_round": 1,
                "max_critic_repair_rounds": 1,
                "formalization_counts": {"formal_gap": 2, "kernel_verified": 0},
                "high_priority_agenda": [
                    {
                        "id": "formal_gap:proof_bank_expansion",
                        "action": "expand proof-bank primitives " + ("detail " * 100),
                        "acceptance_gate": "AXLE/local Lean kernel verifies the promoted obligation",
                    }
                ],
                "formal_subclaim_feedback": [
                    {
                        "id": "coverage_bridge",
                        "status": "FORMAL_GAP",
                        "gap_reason": "missing exchangeability bridge",
                    }
                ],
                "required_revision": "Revise theorem statements and assumptions from critic feedback.",
                "proof_evidence_boundary": "Lean kernel evidence only.",
            },
            "runtime_learning_memory": {
                "source_paths": ["runs/previous/runtime_learning_rows.jsonl"],
                "rows": [
                    {
                        "question_id": "previous_frontier_case",
                        "learning_task": "next_action_routing",
                        "input_summary": {"trigger": "FORMAL_GAP"},
                        "target_behavior": "route non-kernel proof rows to local Lean rerun",
                        "acceptance_gate": "kernel evidence only from local Lean or AXLE",
                    }
                ],
                "counts": {"rows_loaded": 1},
                "boundary": "Prior learning rows are orchestration memory, not proof evidence.",
            },
        },
    )

    assert "full retrieval artifacts remain" in prompt.lower()
    assert "concise_output_budget" in prompt
    assert '"max_derivation_steps":2' in prompt
    assert '"max_next_actions":1' in prompt
    assert "minimal first-pass discovery packet" in prompt
    assert "Probability.coverage" in prompt
    assert "signature_omitted" in prompt
    assert long_signature not in prompt
    assert '"inputs"' not in prompt
    assert '"formal_source_hits":1' in prompt
    assert "CriticEvaluator" in prompt
    assert "formal_gap:proof_bank_expansion" in prompt
    assert "missing exchangeability bridge" in prompt
    assert "Revise theorem statements and assumptions" in prompt
    assert "previous_frontier_case" in prompt
    assert "route non-kernel proof rows" in prompt
    assert "orchestration memory, not proof evidence" in prompt


def test_research_loop_uses_llm_theory_developer_repair_handler() -> None:
    out_dir = Path("runs/test_research_loop_llm_theory_repair")
    shutil.rmtree(out_dir, ignore_errors=True)
    question = load_open_research_questions(Path("examples/research_questions.json"))[0]
    problem = ProblemFormalizer().formalize(question)
    procedures, theorem_goals = TheoryPlanner().plan(problem)
    bad_sim = ResearchSimulator(n_runs=25, seed=13).run(problem, procedures)[0]
    bad_sim.passed = False
    bad_sim.diagnosis.status = "THEORY_OR_PROCEDURE_ISSUE"
    bad_sim.diagnosis.escalate_to = "theory_developer"
    bad_sim.diagnosis.failed_diagnostics = ("coverage",)
    bad_sim.diagnosis.rationale = "test forces LLM theory repair"
    ok_sim = ResearchSimulator(n_runs=25, seed=14).run(problem, procedures)[0]
    ok_sim.passed = True
    ok_sim.diagnosis.status = "OK"
    ok_sim.diagnosis.escalate_to = "none"
    ok_sim.diagnosis.rationale = "test LLM theory repair second round passes"

    first_report = _research_report(
        question=question,
        problem=problem,
        procedures=procedures,
        theorem_goals=theorem_goals,
        simulation=bad_sim,
        agenda_item={
            "id": "simulation:llm-theory",
            "owner_agent": "theory_developer",
            "trigger": "THEORY_OR_PROCEDURE_ISSUE",
            "action": "ask_llm_theory_developer_for_derivation_backed_revision",
            "evidence": "coverage below threshold",
            "failed_diagnostics": ["coverage"],
            "target_procedure": procedures[0].id,
        },
        status="SIMULATION_FLAGGED_WITH_FORMAL_GAPS",
    )
    second_report = _research_report(
        question=question,
        problem=problem,
        procedures=procedures,
        theorem_goals=theorem_goals,
        simulation=ok_sim,
        agenda_item={
            "id": "monitor:llm-theory",
            "owner_agent": "research_coordinator",
            "trigger": "NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
            "action": "archive_trace_or_expand_benchmark_stress_tests",
            "evidence": "test monitor",
        },
        status="RESEARCH_TRACE_READY_WITH_FORMAL_GAPS",
    )
    reports = [first_report, second_report]

    class FakeLab:
        def __init__(self, report):
            self.report = report

        async def run(self, question):
            return self.report

    def factory(n_runs, seed):
        return FakeLab(reports.pop(0))

    developer = LLMTheoryDeveloperAgent(
        provider=StaticArchitectLLMProvider(_sample_response()),
        config=ResearchArchitectConfig(provider_name="static", model="static-theory-model"),
    )
    result = asyncio.run(
        ResearchLoopCoordinator(
            n_runs=25,
            seed=13,
            lab_factory=factory,
            repair_handlers={
                "THEORY_OR_PROCEDURE_ISSUE": LLMTheoryDeveloperRepairHandler(
                    theory_developer=developer,
                    out_dir=out_dir,
                )
            },
            enable_default_theory_developer=False,
        ).iterate(question, max_rounds=2)
    )

    assert result["status"] == "CONVERGED_MONITOR_READY"
    assert result["honesty_boundary"]["executes_registered_live_repair_handlers"]
    assert not result["honesty_boundary"]["executes_default_theory_developer_revision_handler"]
    action = result["rounds"][0]["actions"][0]
    assert action["execution_status"] == "EXECUTED_LLM_THEORY_DEVELOPER_REPAIR"
    assert action["live_repair_handler"] == "LLMTheoryDeveloperRepairHandler"
    assert action["repair_contract_ok"]
    assert action["rerun_requested"]
    artifact = action["repair_artifact"]
    assert artifact["kernel_verified"] is False
    assert artifact["proof_evidence_status"] == THEORY_DERIVATION_NOT_PROOF_EVIDENCE
    assert artifact["llm_theory_derivation_packet"]["source_agent"] == "LLMTheoryDeveloperAgent"
    assert Path(action["llm_theory_artifacts"]["manifest"]).exists()
    assert result["n_theory_revisions"] == 1
    assert result["theory_revisions"][0]["live_repair_handler"] == "LLMTheoryDeveloperRepairHandler"
    assert result["rounds"][1]["actions"][0]["execution_status"] == "EXECUTED_MONITOR"


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
