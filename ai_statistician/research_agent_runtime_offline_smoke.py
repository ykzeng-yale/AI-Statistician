from __future__ import annotations

from copy import deepcopy
import json
import shutil
from pathlib import Path
from typing import Any

from .algorithm_engineer_llm import AlgorithmEngineerConfig, LLMAlgorithmEngineerAgent
from .architect_coordinator_llm import (
    ArchitectCoordinatorConfig,
    LLMArchitectCoordinatorAgent,
)
from .critic_evaluator_llm import CriticEvaluatorConfig, LLMCriticEvaluatorAgent
from .formalizer_llm import FormalizerConfig, LLMFormalizerProofEngineerAgent
from .proof_state_feedback import LocalLeanProofStateFeedbackProvider
from .research_agent_runtime import ResearchAgentRuntimeConfig, run_research_agent_runtime
from .research_architect import (
    LLMTheoryDeveloperAgent,
    ResearchArchitectConfig,
    StaticArchitectLLMProvider,
)
from .research_lab import load_open_research_questions
from .simulation_engineer_llm import (
    LLMSimulationEngineerAgent,
    SimulationEngineerConfig,
)


OFFLINE_RUNTIME_SMOKE_SOURCE = "system_generated_offline_runtime_smoke"
OFFLINE_RUNTIME_SMOKE_BOUNDARY = (
    "This deterministic offline smoke runs the actual AgentRuntime loop with "
    "static generator backends. It exercises orchestration, sandbox execution, "
    "formal-gap routing, critic learning rows, and audit plumbing, but it is not "
    "live Claude/OpenAI evidence and cannot satisfy theorem proof gates."
)


def run_research_agent_runtime_offline_smoke(
    out_dir: Path,
    *,
    question_file: Path = Path("examples/research_questions.json"),
    n_runs: int = 20,
    seed: int = 20260528,
    max_iterations: int = 8,
) -> dict[str, Any]:
    """Run a deterministic real AgentRuntime smoke for system-audit plumbing."""

    if out_dir.exists():
        shutil.rmtree(out_dir)
    questions = load_open_research_questions(question_file)
    if not questions:
        raise ValueError(f"no research questions found in {question_file}")
    question = questions[0]
    manifest = run_research_agent_runtime(
        [question],
        out_dir,
        theory_developer=LLMTheoryDeveloperAgent(
            provider=StaticArchitectLLMProvider(_theory_response()),
            config=ResearchArchitectConfig(
                provider_name="static",
                model="static-theory-offline-smoke",
            ),
        ),
        architect_coordinator=LLMArchitectCoordinatorAgent(
            provider=StaticArchitectLLMProvider(_architect_response()),
            config=ArchitectCoordinatorConfig(
                provider_name="static",
                model="static-architect-offline-smoke",
            ),
        ),
        simulation_engineer=LLMSimulationEngineerAgent(
            provider=StaticArchitectLLMProvider(_simulation_response()),
            config=SimulationEngineerConfig(
                provider_name="static",
                model="static-simulation-offline-smoke",
            ),
        ),
        algorithm_engineer=LLMAlgorithmEngineerAgent(
            provider=StaticArchitectLLMProvider(_algorithm_response()),
            config=AlgorithmEngineerConfig(
                provider_name="static",
                model="static-algorithm-offline-smoke",
            ),
        ),
        formalizer=LLMFormalizerProofEngineerAgent(
            provider=StaticArchitectLLMProvider(_formalizer_response()),
            config=FormalizerConfig(
                provider_name="static",
                model="static-formalizer-offline-smoke",
            ),
        ),
        critic_evaluator=LLMCriticEvaluatorAgent(
            provider=StaticArchitectLLMProvider(_critic_response()),
            config=CriticEvaluatorConfig(
                provider_name="static",
                model="static-critic-offline-smoke",
            ),
        ),
        proof_state_provider=LocalLeanProofStateFeedbackProvider(
            lean_command=("true",)
        ),
        config=ResearchAgentRuntimeConfig(
            n_runs=n_runs,
            seed=seed,
            max_iterations=max_iterations,
            evaluation_mode="system_offline_smoke",
            formal_verification_policy="required",
        ),
    )
    manifest["runtime_audit_source"] = OFFLINE_RUNTIME_SMOKE_SOURCE
    manifest["offline_runtime_smoke"] = True
    manifest["contract_smoke"] = False
    manifest["offline_runtime_smoke_boundary"] = OFFLINE_RUNTIME_SMOKE_BOUNDARY
    manifest["proof_evidence_status"] = "OFFLINE_RUNTIME_SMOKE_NOT_PROOF_EVIDENCE"
    manifest_path = out_dir / "research_agent_runtime_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )
    return manifest


def _architect_response() -> dict[str, Any]:
    return {
        "intake_assessment": {
            "problem_type": "frontier semiparametric causal inference theory",
            "frontier_difficulty": "high",
            "primary_success_criteria": [
                "derive a checkable estimator proposal",
                "route executable checks through AgentRuntime",
                "preserve Lean/kernel proof boundaries",
            ],
            "known_risks": [
                "simulation diagnostics are empirical",
                "formal gaps must remain explicit",
            ],
        },
        "subsystem_execution_plan": [
            {
                "subsystem": "RetrievalMemory",
                "objective": "collect source, knowledge, and formal-source context",
                "inputs_needed": ["open question"],
                "expected_artifacts": ["retrieval_memory_manifest"],
                "acceptance_gate": "retrieval context records source boundaries",
            },
            {
                "subsystem": "TheoryDeveloper",
                "objective": "derive estimator, theorem cards, and proof plan",
                "inputs_needed": ["question", "retrieval context"],
                "expected_artifacts": ["theory_derivation_packet"],
                "acceptance_gate": "schema-valid proposal with no proof claim",
            },
            {
                "subsystem": "SimulationEvaluator",
                "objective": "run registered simulation diagnostics",
                "inputs_needed": ["theory packet"],
                "expected_artifacts": ["simulation_manifest"],
                "acceptance_gate": "runtime records seed and empirical boundary",
            },
            {
                "subsystem": "AlgorithmEngineer",
                "objective": "run sandbox prototypes for implementation gaps",
                "inputs_needed": ["implementation gaps"],
                "expected_artifacts": ["algorithm_sandbox_manifest"],
                "acceptance_gate": "sandbox metrics are reproducible",
            },
            {
                "subsystem": "FormalizationEvaluator",
                "objective": "separate proof-bank rows from formal gaps",
                "inputs_needed": ["theory packet"],
                "expected_artifacts": ["formalization_manifest"],
                "acceptance_gate": "kernel count only comes from verifier rows",
            },
            {
                "subsystem": "CriticEvaluator",
                "objective": "audit evidence boundaries and export learning rows",
                "inputs_needed": ["runtime artifacts"],
                "expected_artifacts": ["critic_evaluator_manifest"],
                "acceptance_gate": "critic agenda preserves proof boundaries",
            },
        ],
        "retrieval_strategy": {
            "paper_queries": ["AIPW semiparametric efficiency cross fitting"],
            "formal_source_queries": ["Slutsky theorem asymptotic normality Lean"],
            "lean_rag_priorities": ["conditional expectation", "positivity"],
        },
        "problem_analysis": {
            "theorem_family": "semiparametric asymptotic normality",
            "statistical_objects": ["ATE", "cross-fit AIPW estimator"],
            "likely_analogy_classes": ["double machine learning"],
            "key_obstacles": ["positivity", "nuisance convergence"],
            "missing_information": ["source theorem matching assumptions"],
        },
        "stat_knowledge_bank_plan": {
            "source_families_to_collect": ["DML/AIPW CLT papers"],
            "assumption_dimensions": ["DGP", "estimand", "positivity"],
            "proof_skeletons_to_track": ["orthogonal decomposition"],
            "failed_attempt_memory_policy": "record blockers as prompt memory",
        },
        "literature_fair_comparison_plan": [
            {
                "candidate_source_family": "double machine learning ATE CLT",
                "must_match": ["estimand", "sample splitting"],
                "likely_mismatches": ["overlap condition strength"],
                "unsafe_transfer_risks": ["borrowing theorem without positivity"],
            }
        ],
        "evidence_contract": {
            "formal_verification_policy": "required",
            "recommended_research_path": "dual_track",
            "formal_required_for_final": True,
            "formal_targets": ["orthogonal score algebra"],
            "simulation_targets": ["finite-sample bias stress test"],
            "acceptance_modes": [
                "final acceptance requires the selected formal target to close"
            ],
            "disclosure_requirements": [
                "distinguish simulation support from Lean proof evidence"
            ],
        },
        "iteration_policy": {
            "reroute_triggers": ["simulation diagnostic failure", "formal gap"],
            "max_repair_rounds": 2,
            "stop_conditions": ["critic agenda records remaining gaps"],
        },
        "evidence_gates": [
            {
                "artifact_kind": "LLM theory packet",
                "required_evidence": "schema validation plus runtime checks",
                "not_evidence": "Lean proof evidence",
            }
        ],
        "risk_register": [
            {
                "risk": "LLM proposal may strengthen assumptions",
                "mitigation": "critic and formalizer surface semantic risks",
                "owner_subsystem": "CriticEvaluator",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "RetrievalMemory",
                "action": "retrieve source and formal context",
                "acceptance_gate": "retrieval manifest is present",
            }
        ],
    }


def _theory_response() -> dict[str, Any]:
    response = {
        "schema_version": 1,
        "artifact_kind": "TheoryDerivationPacket",
        "packet_id": "theory_derivation:offline_smoke",
        "theory_derivation_contract": {
            "min_derivation_steps": 3,
            "min_equation_chain_steps": 2,
            "n_derivation_steps": 3,
            "n_equation_chain_steps": 2,
            "n_assumption_ledger_rows": 3,
            "has_formalization_handoff": True,
            "proof_evidence_status": "THEORY_DERIVATION_NOT_PROOF_EVIDENCE",
        },
        "problem_card": {
            "observed_data": "i.i.d. observations O_i=(X_i,A_i,Y_i)",
            "dgp": "observed-data law with binary treatment",
            "estimand": "psi = E[m_1(X)-m_0(X)]",
            "nuisance_quantities": ["m_a(x)", "e(x)"],
            "assumptions": ["consistency", "exchangeability", "positivity"],
            "asymptotic_regime": "n -> infinity",
            "desired_theorem_type": "asymptotic normality",
        },
        "theory_derivation_packet": {
            "derivation_summary": "Use Neyman-orthogonal AIPW score for the ATE.",
            "derivation_steps": [
                {
                    "id": "identify_ate",
                    "claim": "Exchangeability identifies the ATE.",
                    "equation_or_argument": "psi = E[m_1(X)-m_0(X)]",
                    "depends_on": [],
                    "formal_goal": "aipw_asymptotic_normality",
                    "risk": "positivity must be explicit",
                },
                {
                    "id": "orthogonal_score",
                    "claim": "AIPW score is first-order insensitive to nuisance error.",
                    "equation_or_argument": "phi = m1-m0 + A/e(Y-m1) - (1-A)/(1-e)(Y-m0) - psi",
                    "depends_on": ["identify_ate"],
                    "formal_goal": "second_order_remainder_bound",
                    "risk": "integrability is required",
                },
                {
                    "id": "remainder_control",
                    "claim": "Cross-fitting plus nuisance rates makes the remainder negligible.",
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
                    "justification": "identification under exchangeability",
                    "depends_on": ["identify_ate"],
                },
                {
                    "step_id": "orthogonal_expansion",
                    "lhs": "sqrt(n)(psi_hat-psi)",
                    "relation": "=",
                    "rhs": "sqrt(n) P_n phi + o_p(1)",
                    "justification": "orthogonality and remainder control",
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
                    "risk_if_dropped": "weights diverge",
                },
                {
                    "assumption": "nuisance convergence",
                    "role": "regularity",
                    "used_in": ["remainder_control"],
                    "risk_if_dropped": "remainder may dominate",
                },
            ],
            "sanity_checks": [
                {
                    "id": "generated_probe_interface",
                    "claim_ref": "generated_bias_probe",
                    "check_type": "normalization",
                    "recomputation": (
                        "The deterministic probe returns unscaled finite diagnostics "
                        "from the supplied runtime controls."
                    ),
                    "result": "All declared outputs are finite and unscaled.",
                    "conclusion": "PASS",
                    "depends_on": [],
                }
            ],
            "formalization_handoff": {
                "source_theorem_target": "aipw_asymptotic_normality",
                "candidate_lean_targets": ["bounded_aipw_expansion"],
                "required_definitions": ["conditional_exchangeability", "aipw_score"],
                "lemma_dependencies": ["second_order_remainder_bound"],
                "semantic_alignment_constraints": ["do not drop nuisance remainder"],
            },
        },
        "estimator_specs": [
            {
                "id": "crossfit_aipw",
                "name": "cross-fitted AIPW",
                "formula": "P_n phi_hat + psi_hat",
                "algorithm_sketch": "fit nuisances on folds and evaluate held-out scores",
                "tuning": ["number of folds"],
                "required_assumptions": ["positivity", "nuisance convergence"],
                "estimator_interface_contract": {
                    "request_fields": [
                        {
                            "name": "observations",
                            "meaning": "one replicate of observed treatment-outcome data",
                            "binding": "per_replicate_data",
                        }
                    ],
                    "response_fields": [
                        {
                            "name": "estimate",
                            "meaning": "cross-fitted AIPW estimate of the ATE",
                            "normalization": (
                                "finite-sample point estimate, not root-n scaled"
                            ),
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
            },
            {
                "id": "generated_bias_probe",
                "name": "generated deterministic bias probe",
                "formula": "controlled deterministic Monte Carlo summary",
                "algorithm_sketch": "use a vetted generated Python sandbox draft",
                "tuning": ["replicates"],
                "required_assumptions": ["finite deterministic summary metrics"],
                "estimator_interface_contract": {
                    "request_fields": [
                        {
                            "name": "seed",
                            "meaning": "deterministic runtime seed",
                            "binding": "runtime_control",
                        },
                        {
                            "name": "replicates",
                            "meaning": "bounded runtime replicate count",
                            "binding": "runtime_control",
                        },
                    ],
                    "response_fields": [
                        {
                            "name": "mean_bias_probe",
                            "meaning": "unscaled deterministic probe mean",
                            "normalization": "finite average over runtime replicates",
                            "sample_size_order": "not sample-size indexed",
                            "sample_size_rate": {"scale": "not_indexed"},
                            "derivation_ref": "generated_probe_interface",
                        },
                        {
                            "name": "rmse",
                            "meaning": "unscaled root mean squared probe value",
                            "normalization": "finite root mean square over replicates",
                            "sample_size_order": "not sample-size indexed",
                            "sample_size_rate": {"scale": "not_indexed"},
                            "derivation_ref": "generated_probe_interface",
                        },
                        {
                            "name": "n_runs",
                            "meaning": "consumed runtime replicate count",
                            "normalization": "unscaled integer runtime diagnostic",
                            "sample_size_order": "not sample-size indexed",
                            "sample_size_rate": {"scale": "not_indexed"},
                            "derivation_ref": "generated_probe_interface",
                        },
                    ],
                },
            },
        ],
        "theorem_cards": [
            {
                "id": "aipw_asymptotic_normality",
                "informal_statement": "Cross-fitted AIPW is asymptotically normal under nuisance rates.",
                "assumptions_used": ["exchangeability", "positivity"],
                "conclusion": "sqrt(n)(psi_hat-psi) -> N(0, Var(phi))",
                "rate_or_limit_law": "root-n CLT",
                "proof_strategy": "influence-function expansion plus negligible remainder",
                "semantic_risks": ["formalizing exchangeability faithfully"],
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
                {
                    "from": "second_order_remainder_bound",
                    "to": "aipw_asymptotic_normality",
                }
            ],
            "required_primitives": ["conditional_expectation", "slutsky_theorem"],
            "acceptable_strengthening": ["bounded outcomes for first Lean target"],
            "unacceptable_changes": ["replace exchangeability with randomized treatment"],
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
            "expected_theoretical_behavior": ["coverage approaches nominal"],
        },
        "critic_findings": [
            {
                "critic": "runtime_critic",
                "finding": (
                    "crossfit_aipw needs executable implementation before "
                    "simulation can judge that exact estimator"
                ),
                "reroute_if_confirmed": "AlgorithmEngineer",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "AlgorithmEngineer",
                "action": "implement crossfit_aipw adapter",
                "acceptance_gate": "reproducible simulation manifest",
            }
        ],
    }
    response["interfaces"] = {
        str(row["id"]): deepcopy(row["estimator_interface_contract"])
        for row in response["estimator_specs"]
    }
    return response


def _algorithm_response() -> dict[str, Any]:
    return {
        "theory_trace_alignment": {
            "referenced_derivation_steps": ["orthogonal_score", "remainder_control"],
            "referenced_equation_steps": ["orthogonal_expansion"],
            "referenced_assumptions": ["positivity", "nuisance convergence"],
            "referenced_formalization_targets": ["aipw_asymptotic_normality"],
            "rationale": "implementation metrics track the AIPW score and remainder",
        },
        "implementation_targets": [
            {
                "estimator_id": "crossfit_aipw",
                "adapter_strategy": "Use the registered crossfit_aipw sandbox template.",
                "registered_template_hint": "crossfit_aipw",
                "data_contract": ["observed columns X, A, Y", "binary treatment"],
                "validation_metrics": ["bias", "rmse", "coverage_95", "n_success"],
                "risk_controls": ["clip propensity scores"],
            },
            {
                "estimator_id": "generated_bias_probe",
                "adapter_strategy": "Use a generated Python draft after safety checks.",
                "registered_template_hint": "none",
                "data_contract": ["seed", "replicates"],
                "validation_metrics": ["mean_bias_probe", "rmse", "n_runs"],
                "risk_controls": ["no imports", "sandbox-only output"],
            },
        ],
        "sandbox_plan": {
            "prototype_steps": ["instantiate AIPW template", "record metrics"],
            "stress_tests": ["near positivity violation"],
            "expected_outputs": ["simulation metrics JSON"],
            "expected_failure_modes": ["coverage below target"],
        },
        "code_generation_plan": {
            "files_to_generate": ["sandbox prototype only"],
            "functions_to_implement": ["run_sandbox"],
            "dependencies": ["math"],
            "runtime_executor": "AgentRuntime",
        },
        "sandbox_code_drafts": [
            {
                "estimator_id": "generated_bias_probe",
                "language": "python",
                "entrypoint": "run_sandbox",
                "code": (
                    "import math\n"
                    "def run_sandbox(seed: int, replicates: int) -> dict:\n"
                    "    n = max(5, int(replicates))\n"
                    "    total = 0.0\n"
                    "    sq_total = 0.0\n"
                    "    for i in range(n):\n"
                    "        value = float(((int(seed) + i * 17) % 101)) / 100.0 - 0.5\n"
                    "        total = total + value\n"
                    "        sq_total = sq_total + value * value\n"
                    "    mean = total / float(n)\n"
                    "    variance = sq_total / float(n) - mean * mean\n"
                    "    if variance < 0.0:\n"
                    "        variance = 0.0\n"
                    "    return {'status': 'ok', 'n_runs': n, 'mean_bias_probe': mean, 'rmse': math.sqrt(variance + mean * mean), 'sandbox_failed': False}\n"
                ),
                "intended_metrics": ["mean_bias_probe", "rmse", "n_runs"],
                "safety_notes": ["no filesystem access", "AgentRuntime executes"],
            }
        ],
        "promotion_gate": {
            "required_tests": ["sandbox smoke passes"],
            "required_reproducibility_evidence": ["fixed seed"],
            "production_registration_requirements": ["registry entry"],
        },
        "critic_findings": [
            {
                "critic": "implementation_boundary",
                "finding": "The prototype must remain sandbox-only until promoted.",
                "reroute_if_confirmed": "AlgorithmEngineer",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "AgentRuntime",
                "action": "execute sandbox template",
                "acceptance_gate": "reproducible sandbox metrics recorded",
            }
        ],
    }


def _simulation_response() -> dict[str, Any]:
    return {
        "theory_trace_alignment": {
            "referenced_derivation_steps": ["identify_ate", "remainder_control"],
            "referenced_equation_steps": ["identified_estimand", "orthogonal_expansion"],
            "referenced_assumptions": ["positivity", "nuisance convergence"],
            "referenced_formalization_targets": ["aipw_asymptotic_normality"],
            "rationale": "DGPs target identification, overlap, and remainder anchors",
        },
        "simulation_targets": [
            {
                "procedure_id": "aipw_crossfit",
                "estimand": "average treatment effect",
                "primary_question": "Does AIPW achieve nominal coverage under overlap?",
                "target_theorem_card": "aipw_asymptotic_normality",
            }
        ],
        "dgp_plan": [
            {
                "id": "well_overlapped_binary_treatment",
                "description": "Binary treatment DGP with bounded propensity.",
                "parameters": ["n", "overlap bound", "outcome noise"],
                "assumptions_stressed": ["positivity", "nuisance rate"],
                "expected_behavior": "coverage should approach nominal",
            }
        ],
        "metric_plan": ["bias", "rmse", "coverage_95"],
        "stress_tests": ["near-positivity violation"],
        "failure_interpretation": [
            {
                "diagnostic": "coverage below target",
                "possible_cause": "positivity failure",
                "reroute_to": "TheoryDeveloper",
            }
        ],
        "runtime_execution_plan": {
            "registered_simulator": "ResearchSimulator.run",
            "n_runs": 20,
            "seed": 20260528,
            "notes": ["AgentRuntime owns execution and records metrics."],
        },
        "simulation_code_drafts": [
            {
                "simulation_id": "generated_aipw_coverage_probe",
                "language": "python",
                "entrypoint": "run_sandbox",
                "code": (
                    "import math\n"
                    "def run_sandbox(seed: int, replicates: int) -> dict:\n"
                    "    n = max(5, int(replicates))\n"
                    "    covered = 0\n"
                    "    sq_total = 0.0\n"
                    "    total = 0.0\n"
                    "    for i in range(n):\n"
                    "        centered = float(((int(seed) + i * 37) % 41) - 20) / 1000.0\n"
                    "        total = total + centered\n"
                    "        sq_total = sq_total + centered * centered\n"
                    "        if abs(centered) <= 0.06:\n"
                    "            covered = covered + 1\n"
                    "    mean_bias = total / float(n)\n"
                    "    mse = sq_total / float(n)\n"
                    "    return {\n"
                    "        'status': 'ok',\n"
                    "        'n_runs': n,\n"
                    "        'coverage_95': float(covered) / float(n),\n"
                    "        'target_coverage': 0.95,\n"
                    "        'mean_bias': mean_bias,\n"
                    "        'rmse': math.sqrt(mse),\n"
                    "        'sandbox_failed': False,\n"
                    "    }\n"
                ),
            }
        ],
        "critic_findings": [
            {
                "critic": "simulation_critic",
                "finding": "Simulation evidence remains empirical and not proof.",
                "reroute_if_confirmed": "FormalizationEvaluator",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "AgentRuntime",
                "action": "run registered simulator",
                "acceptance_gate": "simulation manifest records metrics",
            }
        ],
    }


def _formalizer_response() -> dict[str, Any]:
    return {
        "theory_trace_alignment": {
            "referenced_derivation_steps": ["orthogonal_score", "remainder_control"],
            "referenced_equation_steps": ["orthogonal_expansion"],
            "referenced_assumptions": ["exchangeability", "nuisance convergence"],
            "referenced_formalization_targets": [
                "aipw_asymptotic_normality",
                "second_order_remainder_bound",
            ],
            "rationale": "formal targets preserve AIPW expansion and theorem target",
        },
        "formal_targets": [
            {
                "id": "lean_aipw_asymptotic_normality_open_target",
                "informal_source": "AIPW asymptotic normality theorem card",
                "lean_statement_sketch": "theorem aipw_asymptotic_normality_open_target ...",
                "semantic_alignment_constraints": ["do not drop nuisance remainder"],
                "expected_status": "OPEN",
            }
        ],
        "lemma_dependency_plan": [
            {
                "from": "second_order_remainder_bound",
                "to": "aipw_asymptotic_normality",
                "role": "reduce estimator expansion to CLT plus negligible remainder",
                "risk": "asymptotic primitives may be missing",
            }
        ],
        "retrieval_queries": [
            {
                "query": "Slutsky theorem asymptotic normality Lean StatInference",
                "target_library": "StatInference",
                "purpose": "find convergence bridge primitives",
            }
        ],
        "proof_search_plan": {
            "preferred_tools": ["formal_source_retriever", "proof_bank"],
            "tactic_or_certificate_hints": ["start with bounded helper lemmas"],
            "kernel_check_plan": ["run FormalSubclaimProver for promoted candidate"],
            "known_blockers": ["exchangeability formalization", "asymptotics"],
        },
        "proof_bank_obligation_requests": [
            {
                "obligation_id": "variance_nonneg",
                "target_theorem_card": "aipw_asymptotic_normality",
                "reason": "representative registered kernel-smoke dependency",
                "verification_priority": "high",
            }
        ],
        "gap_taxonomy": [
            {
                "gap": "conditional exchangeability source theorem",
                "kind": "formal_primitives",
                "next_owner": "Formalizer/LeanProver",
            }
        ],
        "critic_findings": [
            {
                "critic": "proof_boundary_critic",
                "finding": "Static proof rows must not be promoted to kernel evidence.",
                "reroute_if_confirmed": "FormalizationEvaluator",
            }
        ],
        "next_actions": [
            {
                "owner_agent": "FormalizationEvaluator",
                "action": "run proof-bank subclaims and preserve formal gaps",
                "acceptance_gate": "formalization manifest records gaps separately",
            }
        ],
    }


def _critic_response() -> dict[str, Any]:
    return {
        "evidence_boundary_audit": [
            {
                "artifact_id": "formalization_manifest",
                "evidence_type": "formalization_proof_feedback",
                "boundary_ok": True,
                "risk": "proved rows are non-kernel unless local Lean rerun records evidence",
                "required_followup": "run kernel rerun queue before proof claims",
            }
        ],
        "reroute_recommendations": [
            {
                "owner_subsystem": "Formalizer/LeanProver",
                "trigger": "FORMAL_GAP",
                "action": "expand proof-bank primitives",
                "priority": "high",
                "acceptance_gate": "local Lean verifies promoted obligations",
            }
        ],
        "critic_findings": [
            {
                "critic": "evidence_boundary_critic",
                "finding": "Open formal gaps require a kernel-checked follow-up.",
                "reroute_if_confirmed": "Formalizer/LeanProver",
            }
        ],
        "learning_updates": [
            {
                "learning_task": "proof_boundary_preservation",
                "input_signal": "formalization counts include gaps",
                "target_behavior": "route to kernel rerun instead of claiming proof",
                "negative_example": "treating static proof-bank rows as theorem proof",
            }
        ],
        "benchmark_expansion_plan": [
            {
                "benchmark_item": "hard-mode AIPW theorem discovery",
                "capability_target": "discover theorem then preserve proof gaps",
                "success_evidence": "separate discovery, simulation, and kernel counts",
            }
        ],
        "kernel_evidence_requirements": [
            "AXLE/local Lean verification of each promoted obligation"
        ],
        "next_actions": [
            {
                "owner_agent": "Formalizer/LeanProver",
                "action": "run kernel proof smoke on representative rows",
                "acceptance_gate": "kernel_verified count comes from local Lean",
            }
        ],
    }
