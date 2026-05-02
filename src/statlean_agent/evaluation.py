"""Benchmark evaluation helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from statlean_agent.contracts import (
    BenchmarkTask,
    EvalReport,
    ProofAttempt,
    RewardBreakdown,
    VerificationReport,
    VerificationStatus,
)
from statlean_agent.rewards import aggregate_reward_breakdowns, scan_policy_tokens, score_attempt


DEFAULT_PAPER_QUALITY_PROOF_CHAINS = (
    {
        "chain_id": "ipw_hajek_linearization_chain",
        "name": "IPW/Hajek identification plus scaled linearization",
        "source_module": "StatInference.Causal.IPW",
        "benchmark_task_ids": (
            "ipw_identification_certificate_seed",
            "ipw_hajek_scaled_linearization_route_seed",
            "constant_ipw_hajek_route_seed",
            "constant_ipw_hajek_exact_target_seed",
            "paper_quality_ipw_hajek_concrete_chain_seed",
        ),
        "required_declarations": (
            "StatInference.IPWHajekLinearizationRoute.identifies",
            "StatInference.IPWHajekLinearizationRoute.scaledLinearization",
            "StatInference.constantIPWHajekLinearizationRoute",
            "StatInference.paperQualityIPWHajekConcreteEstimatorChain",
        ),
    },
    {
        "chain_id": "aipw_product_rate_chain",
        "name": "AIPW double robustness plus orthogonal product-rate remainder",
        "source_module": "StatInference.Causal.AIPW",
        "benchmark_task_ids": (
            "aipw_double_robust_identification_seed",
            "aipw_product_rate_remainder_seed",
            "aipw_orthogonal_score_seed",
            "aipw_second_order_remainder_seed",
            "trivial_aipw_product_rate_route_seed",
        ),
        "required_declarations": (
            "StatInference.AIPWOrthogonalProductRateRoute.identifies",
            "StatInference.AIPWOrthogonalProductRateRoute.secondOrderRemainderSmall",
            "StatInference.trivialAIPWOrthogonalProductRateRoute",
        ),
    },
    {
        "chain_id": "influence_function_normality_chain",
        "name": "Influence-function asymptotic-linearity and normality route",
        "source_module": "StatInference.Semiparametric.Normality",
        "benchmark_task_ids": (
            "influence_function_normality_route_seed",
            "influence_function_normality_bridge_seed",
            "aipw_influence_function_normality_route_seed",
            "trivial_influence_function_normality_seed",
            "trivial_aipw_influence_function_normality_seed",
        ),
        "required_declarations": (
            "StatInference.InfluenceFunctionNormalityRoute.asymptoticLinear",
            "StatInference.InfluenceFunctionNormalityRoute.asymptoticNormal",
            "StatInference.AIPWInfluenceFunctionNormalityRoute.asymptoticNormal",
        ),
    },
)

DEFAULT_REPRODUCIBILITY_ARTIFACTS = (
    "config/statlean_blueprint.json",
    "benchmarks/seeds.jsonl",
    "artifacts/verification/benchmark-seed-reports.jsonl",
    "artifacts/evaluation/benchmark-seed-attempts.jsonl",
    "artifacts/evaluation/benchmark-seed-summary.json",
    "artifacts/evaluation/heldout-baseline.json",
    "artifacts/evaluation/paper-quality-heldout.json",
    "artifacts/evaluation/concrete-estimator-chain.json",
    "artifacts/evaluation/ablation-report.json",
    "artifacts/evaluation/external-baseline-plan.json",
    "artifacts/evaluation/external-baseline-results.json",
    "artifacts/evaluation/empirical-process-targets.json",
    "artifacts/evaluation/empirical-process-external-slice.json",
    "artifacts/research/vdvw-theorem-inventory.json",
    "artifacts/research/vdvw-bracketing-gc-statement-candidates.json",
    "artifacts/research/vdvw-vc-donsker-proof-obligations.json",
    "artifacts/research/vdvw-primitive-empirical-semantics.json",
    "artifacts/training/manifest.json",
    "artifacts/training/dpo-negative-attempts.jsonl",
    "artifacts/training/dpo-negative-reports.jsonl",
    "artifacts/training/grpo-process-tasks.jsonl",
    "artifacts/curation/theorem-hole-ledger.jsonl",
    "artifacts/curation/lemma-proposals.jsonl",
    "artifacts/curation/theorem-hole-promotion-queue.json",
    "artifacts/curation/lemma-proposal-gates.jsonl",
    "artifacts/curation/lemma-non-vacuity.jsonl",
    "artifacts/curation/lemma-proof-cost.jsonl",
    "docs/paper_draft.md",
)

DEFAULT_EMPIRICAL_PROCESS_EXPANSION_TARGETS = (
    {
        "target_id": "bracketing_gc_interface",
        "interface_family": "bracketing",
        "status": "interface_scoped",
        "lean_module": "StatInference.EmpiricalProcess.Complexity",
        "lean_declarations": (
            "StatInference.BracketingNumberSpec",
            "StatInference.BracketingDeviationCertificate",
            "StatInference.BracketingDeviationCertificate.toGlivenkoCantelliClass",
            "StatInference.BracketingDeviationCertificate.uniformDeviation",
            "StatInference.FiniteBracketSampleAverageSemantics",
            "StatInference.FiniteBracketSampleAverageSemantics.toGlivenkoCantelliClass",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toGlivenkoCantelliClass",
        ),
        "depends_on": (
            "StatInference.EmpiricalDeviationSequenceOn",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_tags": ("empirical_process", "glivenko_cantelli"),
        "next_lemma_candidates": (
            "bracketing_entropy_to_uniform_deviation",
            "finite_bracketing_number_to_gc_class",
        ),
    },
    {
        "target_id": "vc_subgraph_gc_interface",
        "interface_family": "vc_subgraph",
        "status": "interface_scoped",
        "lean_module": "StatInference.EmpiricalProcess.VCSubgraph",
        "lean_declarations": (
            "StatInference.VCSubgraphSpec",
            "StatInference.VCDeviationCertificate",
            "StatInference.VCDeviationCertificate.toGlivenkoCantelliClass",
            "StatInference.VCDeviationCertificate.uniformDeviation",
            "StatInference.VCSubgraphProofObligations",
            "StatInference.VCSubgraphGCRoute",
            "StatInference.VCSubgraphGCRoute.toVCDeviationCertificate",
            "StatInference.VCSubgraphGCRoute.toGlivenkoCantelliClass",
        ),
        "depends_on": (
            "StatInference.EmpiricalDeviationSequenceOn",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_tags": ("empirical_process", "vc_subgraph", "glivenko_cantelli"),
        "next_lemma_candidates": (
            "vc_subgraph_shatter_bound_to_uniform_deviation",
            "vc_subgraph_bounded_envelope_to_gc_class",
        ),
    },
    {
        "target_id": "donsker_bridge_interface",
        "interface_family": "donsker",
        "status": "interface_scoped",
        "lean_module": "StatInference.EmpiricalProcess.Donsker",
        "lean_declarations": (
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerBridgeCertificate.toGlivenkoCantelliClass",
            "StatInference.DonskerBridgeCertificate.weakConvergence",
            "StatInference.DonskerAsymptoticNormalityRoute",
            "StatInference.DonskerAsymptoticNormalityRoute.estimatorCLT",
            "StatInference.DonskerAsymptoticNormalityRoute.asymptoticNormal",
            "StatInference.trivialDonskerAsymptoticNormalityRoute",
        ),
        "depends_on": (
            "StatInference.GlivenkoCantelliClass",
            "StatInference.DonskerSpec",
        ),
        "benchmark_tags": ("empirical_process", "donsker"),
        "next_lemma_candidates": (
            "asymptotic_equipartition_to_donsker_bridge",
            "donsker_bridge_to_statistical_inference_clt_route",
        ),
    },
    {
        "target_id": "covering_number_gc_interface",
        "interface_family": "covering_number",
        "status": "implemented_seed_interface",
        "lean_module": "StatInference.EmpiricalProcess.Complexity",
        "lean_declarations": (
            "StatInference.CoveringNumberSpec",
            "StatInference.CoveringNumberDeviationCertificate",
            "StatInference.CoveringNumberDeviationCertificate.toGlivenkoCantelliClass",
        ),
        "depends_on": (
            "StatInference.EmpiricalDeviationSequenceOn",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_tags": ("empirical_process", "covering_number", "glivenko_cantelli"),
        "next_lemma_candidates": (
            "covering_entropy_to_uniform_deviation",
            "covering_certificate_non_vacuity_examples",
        ),
    },
    {
        "target_id": "rademacher_gc_interface",
        "interface_family": "rademacher_complexity",
        "status": "implemented_seed_interface",
        "lean_module": "StatInference.EmpiricalProcess.Complexity",
        "lean_declarations": (
            "StatInference.RademacherComplexitySpec",
            "StatInference.RademacherDeviationCertificate",
            "StatInference.RademacherDeviationCertificate.toGlivenkoCantelliClass",
            "StatInference.RademacherDeviationCertificate.radius_tendsto_zero",
        ),
        "depends_on": (
            "StatInference.EmpiricalDeviationSequenceOn",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_tags": (
            "empirical_process",
            "rademacher_complexity",
            "glivenko_cantelli",
        ),
        "next_lemma_candidates": (
            "symmetrization_to_rademacher_deviation",
            "rademacher_certificate_non_vacuity_examples",
        ),
    },
)

DEFAULT_EMPIRICAL_PROCESS_EXTERNAL_FAMILIES = (
    "bracketing",
    "vc_subgraph",
    "donsker",
)

VDVW_MARKDOWN_ROOT = (
    "Math Textbook Foundation/Vaart 1996 Weak Convergence and Emperical "
    "Process(1)/Markdown"
)

DEFAULT_VDVW_THEOREM_INVENTORY = (
    {
        "inventory_id": "vdvw-2.4.1-finite-bracketing-gc",
        "source_label": "Theorem 2.4.1",
        "kind": "Theorem",
        "title": "Finite L1 bracketing implies Glivenko-Cantelli",
        "chapter": "2.4",
        "source_segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "source_line_start": 970,
        "source_line_end": 970,
        "textbook_paraphrase": (
            "A measurable function class with finite L1(P) bracketing number "
            "at every positive radius is Glivenko-Cantelli."
        ),
        "interface_family": "bracketing",
        "formalization_tier": "primitive_candidate",
        "current_claim_level": "deterministic_reduction_plus_certificate_interface",
        "current_lean_declarations": (
            "StatInference.FiniteL1BracketingFamily",
            "StatInference.L1BracketingNumberWitness",
            "StatInference.L1BracketingNumberFiniteAt",
            "StatInference.FiniteL1BracketingNumberAtEveryScale",
            "StatInference.L1BracketingNumberConstructorObligations",
            "StatInference.L1BracketingSequenceRoute",
            "StatInference.empiricalDeviationBoundOn_of_bracket_endpoint_bounds",
            "StatInference.finite_endpoint_strong_law_eventually_abs_le_real",
            "StatInference.L1BracketingSequenceRoute.toGlivenkoCantelliClass",
            "StatInference.L1BracketingNumberConstructorObligations.toGlivenkoCantelliClass",
            "StatInference.FiniteBracketEndpointStrongLawAssembly",
            "StatInference.FiniteBracketEndpointStrongLawAssembly.toGlivenkoCantelliClass",
            "StatInference.bracketEndpointEmpiricalAverage",
            "StatInference.bracketEndpointEmpiricalSequence",
            "StatInference.FiniteBracketSampleAverageSemantics",
            "StatInference.FiniteBracketSampleAverageSemantics.toEndpointStrongLawAssembly",
            "StatInference.FiniteBracketSampleAverageSemantics.toGlivenkoCantelliClass",
            "StatInference.bracketEndpointPopulationIntegral",
            "StatInference.bracketEndpointEmpiricalMeasureSequence",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toEndpointStrongLawAssembly",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toGlivenkoCantelliClass",
            "StatInference.OuterProbabilitySpace",
            "StatInference.OuterTendstoInProbability",
            "StatInference.OuterAlmostSureTendsto",
            "StatInference.OuterSupremumDeviation",
        ),
        "benchmark_task_ids": (
            "bracketing_deterministic_bound_seed",
            "finite_endpoint_strong_law_eventual_bound_seed",
            "l1_bracketing_sequence_gc_seed",
            "finite_l1_bracketing_number_at_scale_seed",
            "finite_l1_bracketing_every_scale_projection_seed",
            "finite_l1_bracketing_number_constructor_seed",
            "finite_bracket_endpoint_control_constructor_seed",
            "finite_bracket_endpoint_control_gc_seed",
            "finite_bracket_sample_average_assembly_seed",
            "finite_bracket_sample_average_constructor_seed",
            "finite_bracket_sample_average_gc_seed",
            "finite_bracket_empirical_measure_assembly_seed",
            "finite_bracket_empirical_measure_constructor_seed",
            "finite_bracket_empirical_measure_gc_seed",
            "outer_probability_space_monotone_seed",
            "outer_gc_projection_seed",
            "vdvw_2_4_1_current_gc_bridge_seed",
            "trivial_bracketing_gc_non_vacuity_seed",
        ),
        "missing_definitions": (
            "measurable function class over an iid sample space",
            "measure-backed L1(P) seminorm tying bracket width to endpoint functions",
            "empirical measure P_n as a probability measure",
            "outer-probability norm ||P_n - P||*_F and almost-sure GC convergence mode",
        ),
        "semantic_risks": (
            "Current Lean route proves the deterministic finite-bracketing handoff and sample-average endpoint assembly but still does not prove the outer almost-sure theorem.",
            "Measurability and outer-probability bookkeeping are still abstract.",
            "Endpoint strong-law wrappers do not yet assemble the full almost-sure uniform convergence theorem.",
        ),
        "next_actions": (
            "Tie the proof-carrying L1 bracketing-number witness to a measure-backed L1(P) seminorm.",
            "Connect finite endpoint SLLN and deterministic bracket bounds into the full Theorem 2.4.1 convergence statement.",
        ),
    },
    {
        "inventory_id": "vdvw-2.4.3-random-entropy-gc",
        "source_label": "Theorem 2.4.3",
        "kind": "Theorem",
        "title": "Random entropy condition implies Glivenko-Cantelli",
        "chapter": "2.4",
        "source_segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "source_line_start": 988,
        "source_line_end": 988,
        "textbook_paraphrase": (
            "A P-measurable class with integrable envelope and suitable random "
            "L1 empirical covering growth is Glivenko-Cantelli."
        ),
        "interface_family": "bracketing",
        "formalization_tier": "dependency_heavy_theorem_card",
        "current_claim_level": "certificate_interface",
        "current_lean_declarations": (
            "StatInference.CoveringNumberDeviationCertificate",
            "StatInference.BracketingDeviationCertificate",
            "StatInference.GlivenkoCantelliClass",
        ),
        "benchmark_task_ids": (
            "covering_certificate_gc_seed",
            "bracketing_certificate_gc_seed",
        ),
        "missing_definitions": (
            "P-measurable classes and outer expectation/probability",
            "empirical random covering numbers over L1(P_n)",
            "integrable envelope and truncation class F_M",
            "outer almost-sure and outer mean convergence conclusions",
        ),
        "semantic_risks": (
            "This theorem is not a bracketing theorem; mapping it into bracketing APIs would drop random entropy assumptions.",
            "The current covering certificate only stores a future deviation proof and is not evidence for random entropy.",
        ),
        "next_actions": (
            "Keep as a theorem card until outer probability and random covering-number infrastructure exist.",
        ),
    },
    {
        "inventory_id": "vdvw-2.5.2-uniform-entropy-donsker",
        "source_label": "Theorem 2.5.2",
        "kind": "Theorem",
        "title": "Uniform entropy condition implies P-Donsker",
        "chapter": "2.5",
        "source_segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "source_line_start": 1106,
        "source_line_end": 1106,
        "textbook_paraphrase": (
            "A measurable function class satisfying the uniform entropy bound "
            "and square-integrable envelope assumptions is P-Donsker."
        ),
        "interface_family": "donsker",
        "formalization_tier": "dependency_heavy_theorem_card",
        "current_claim_level": "certificate_interface",
        "current_lean_declarations": (
            "StatInference.DonskerSpec",
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerAsymptoticNormalityRoute",
        ),
        "benchmark_task_ids": (
            "donsker_statement_seed",
            "donsker_bridge_gc_projection_seed",
            "donsker_bridge_estimator_clt_seed",
        ),
        "missing_definitions": (
            "uniform entropy bound for all finitely discrete Q",
            "L2(P) semimetric and F_delta measurability",
            "empirical-process weak convergence in ell-infinity of a class",
            "tight Brownian bridge or pre-Gaussian limit process",
        ),
        "semantic_risks": (
            "Donsker cannot be inferred from GC; it needs weak convergence and tightness infrastructure.",
            "Current DonskerSpec is a stored weak-convergence statement, not a constructor from entropy.",
        ),
        "next_actions": (
            "Add theorem-hole cards for uniform entropy and asymptotic equicontinuity obligations before any Lean statement promotion.",
        ),
    },
    {
        "inventory_id": "vdvw-2.5.6-bracketing-donsker",
        "source_label": "Theorem 2.5.6",
        "kind": "Theorem",
        "title": "Bracketing entropy integral implies P-Donsker",
        "chapter": "2.5",
        "source_segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "source_line_start": 1204,
        "source_line_end": 1211,
        "textbook_paraphrase": (
            "Finite bracketing and covering entropy integrals plus a weak second "
            "moment envelope imply the function class is P-Donsker."
        ),
        "interface_family": "donsker",
        "formalization_tier": "dependency_heavy_theorem_card",
        "current_claim_level": "certificate_interface",
        "current_lean_declarations": (
            "StatInference.BracketingNumberSpec",
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerAsymptoticNormalityRoute.asymptoticNormal",
        ),
        "benchmark_task_ids": (
            "bracketing_certificate_gc_seed",
            "donsker_asymptotic_normality_handoff_seed",
            "trivial_donsker_asymptotic_normality_seed",
        ),
        "missing_definitions": (
            "L2 and weak-L2 bracketing entropy integrals",
            "weak second moment envelope condition",
            "nested partitions and chaining construction",
            "Donsker weak convergence target in function space",
        ),
        "semantic_risks": (
            "Bracketing GC infrastructure is insufficient for bracketing Donsker.",
            "The current asymptotic-normality handoff consumes a Donsker proof field rather than proving it.",
        ),
        "next_actions": (
            "Defer proof promotion until P-Donsker semantics and entropy-integral APIs exist.",
        ),
    },
    {
        "inventory_id": "vdvw-2.6.4-vc-set-entropy",
        "source_label": "Theorem 2.6.4",
        "kind": "Theorem",
        "title": "VC set classes have polynomial covering numbers",
        "chapter": "2.6",
        "source_segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "source_line_start": 1378,
        "source_line_end": 1383,
        "textbook_paraphrase": (
            "VC classes of sets satisfy a universal polynomial Lr(Q) covering-number bound."
        ),
        "interface_family": "vc_subgraph",
        "formalization_tier": "primitive_dependency_candidate",
        "current_claim_level": "proof_obligation_metadata",
        "current_lean_declarations": (
            "StatInference.VCSubgraphProofObligations",
            "StatInference.VCSubgraphSpec",
            "StatInference.VCSubgraphGCRoute",
        ),
        "benchmark_task_ids": (
            "vc_deviation_certificate_gc_seed",
            "vc_subgraph_route_certificate_seed",
            "trivial_vc_subgraph_gc_non_vacuity_seed",
        ),
        "missing_definitions": (
            "VC class of sets and VC index/dimension",
            "shattering and Sauer-type growth bounds",
            "Lr(Q) covering numbers for indicator set classes",
            "universal-constant handling for entropy bounds",
        ),
        "semantic_risks": (
            "Current VC route records obligations but proves no combinatorial VC theorem.",
            "Function-class VC-subgraph results depend on this set-class entropy layer.",
        ),
        "next_actions": (
            "Create theorem-hole candidates for shattering, Sauer bound, and set-class covering-number translation.",
        ),
    },
    {
        "inventory_id": "vdvw-2.6.7-vc-subgraph-entropy",
        "source_label": "Theorem 2.6.7",
        "kind": "Theorem",
        "title": "VC-subgraph function classes have envelope-scaled covering bounds",
        "chapter": "2.6",
        "source_segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "source_line_start": 1490,
        "source_line_end": 1497,
        "textbook_paraphrase": (
            "VC-subgraph classes with measurable envelope satisfy an envelope-scaled Lr(Q) covering bound."
        ),
        "interface_family": "vc_subgraph",
        "formalization_tier": "primitive_dependency_candidate",
        "current_claim_level": "proof_obligation_metadata",
        "current_lean_declarations": (
            "StatInference.VCSubgraphProofObligations",
            "StatInference.VCDeviationCertificate",
            "StatInference.VCSubgraphGCRoute.toVCDeviationCertificate",
        ),
        "benchmark_task_ids": (
            "vc_subgraph_route_certificate_seed",
            "vc_deviation_certificate_gc_seed",
        ),
        "missing_definitions": (
            "subgraph set for real-valued functions",
            "measurable envelope function",
            "Fubini/Lebesgue-measure product argument for subgraphs",
            "envelope-scaled covering-number statements",
        ),
        "semantic_risks": (
            "Dropping envelope measurability or positivity would make the formal theorem wrong.",
            "The existing VCDeviationCertificate is only a handoff from a supplied deviation proof.",
        ),
        "next_actions": (
            "Represent VC-subgraph entropy as obligations before claiming GC or Donsker consequences.",
        ),
    },
    {
        "inventory_id": "vdvw-2.6.8-vc-subgraph-donsker",
        "source_label": "Theorem 2.6.8",
        "kind": "Theorem",
        "title": "Pointwise separable pre-Gaussian VC classes with weak envelope tail are Donsker",
        "chapter": "2.6",
        "source_segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "source_line_start": 1520,
        "source_line_end": 1520,
        "textbook_paraphrase": (
            "A pointwise separable, P-pre-Gaussian VC function class with a weak second-moment tail envelope is P-Donsker."
        ),
        "interface_family": "donsker",
        "formalization_tier": "late_stage_theorem_card",
        "current_claim_level": "certificate_interface",
        "current_lean_declarations": (
            "StatInference.VCSubgraphGCRoute",
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerAsymptoticNormalityRoute",
        ),
        "benchmark_task_ids": (
            "vc_subgraph_route_certificate_seed",
            "donsker_bridge_estimator_clt_seed",
            "donsker_asymptotic_normality_handoff_seed",
        ),
        "missing_definitions": (
            "pointwise separability",
            "P-pre-Gaussian process indexed by a class",
            "weak second-moment envelope tail condition",
            "Donsker constructor from VC entropy plus pre-Gaussianity",
        ),
        "semantic_risks": (
            "This theorem has stronger assumptions than ordinary VC-subgraph GC.",
            "Current code must not collapse VC-subgraph GC and VC-subgraph Donsker into one certificate.",
        ),
        "next_actions": (
            "Keep as a source-linked theorem card until the Donsker layer is formalized.",
        ),
    },
)

DEFAULT_VDVW_BRACKETING_GC_SOURCE_ANCHORS = (
    {
        "anchor_id": "vdvw-gc-definition",
        "label": "Glivenko-Cantelli class definition",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_1-100.md",
        "line_start": 1834,
        "line_end": 1834,
        "purpose": "identifies the outer-probability or outer-almost-sure convergence target",
    },
    {
        "anchor_id": "vdvw-2.1.6-bracketing-number",
        "label": "Definition 2.1.6",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_1-100.md",
        "line_start": 1895,
        "line_end": 1895,
        "purpose": "defines brackets, epsilon-brackets, and bracketing numbers",
    },
    {
        "anchor_id": "vdvw-2.4.1-statement-proof",
        "label": "Theorem 2.4.1",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 970,
        "line_end": 985,
        "purpose": "states finite L1(P) bracketing implies Glivenko-Cantelli and sketches the finite-bracket/SLLN proof",
    },
)

DEFAULT_VDVW_BRACKETING_GC_STATEMENT_CANDIDATES = (
    {
        "candidate_id": "vdvw-2.4.1-dependency-minimal-sequence-route",
        "track": "dependency_minimal",
        "status": "compiled_bridge_available",
        "statement_kind": "current Lean bridge theorem layer",
        "target_lean_names": (
            "StatInference.L1BracketingSequenceRoute.toGlivenkoCantelliClass",
        ),
        "formal_statement_sketch": (
            "Given a shrinking sequence of finite L1 bracketing families and "
            "endpoint empirical-process bounds tending to zero, construct "
            "GlivenkoCantelliClass indexClass populationRisk empiricalRisk."
        ),
        "required_primitives": (
            "FiniteL1BracketingFamily",
            "L1BracketingSequenceRoute",
            "EmpiricalDeviationSequenceOn",
            "GlivenkoCantelliClass",
        ),
        "proof_obligations": (
            "show endpointRadius tends to zero",
            "show bracket family scale tends to zero",
            "apply deterministic bracket endpoint bound at each sample size",
        ),
        "existing_lean_handoffs": (
            "StatInference.empiricalDeviationBoundOn_of_bracket_endpoint_bounds",
            "StatInference.L1BracketingSequenceRoute.toEmpiricalDeviationSequenceOn",
            "StatInference.L1BracketingSequenceRoute.toGlivenkoCantelliClass",
        ),
        "benchmark_task_ids": (
            "bracketing_deterministic_bound_seed",
            "l1_bracketing_sequence_gc_seed",
            "trivial_bracketing_gc_non_vacuity_seed",
        ),
        "local_lake_validation_hooks": (
            "lake build",
            "render benchmark task l1_bracketing_sequence_gc_seed",
            "verify benchmark task l1_bracketing_sequence_gc_seed",
        ),
        "axle_validation_hooks": (
            "extract_decls on StatInference/EmpiricalProcess/L1Bracketing.lean",
            "check rendered l1_bracketing_sequence_gc_seed in AXLE lean environment",
        ),
        "semantic_risks": (
            "This is not the exact Theorem 2.4.1 statement because it assumes a shrinking bracketing route instead of deriving one from N_[] finite for every epsilon.",
        ),
        "promotion_gate": (
            "Keep as bridge layer until primitive bracketing-number and endpoint-SLLN constructors exist.",
        ),
    },
    {
        "candidate_id": "vdvw-2.4.1-primitive-l1-bracketing-number",
        "track": "dependency_minimal",
        "status": "compiled_signature_available",
        "statement_kind": "compiled primitive constructor signature candidate",
        "target_lean_names": (
            "StatInference.L1BracketingNumberWitness",
            "StatInference.FiniteL1BracketingNumberAtEveryScale",
            "StatInference.L1BracketingNumberConstructorObligations",
            "StatInference.L1BracketingNumberConstructorObligations.toGlivenkoCantelliClass",
        ),
        "formal_statement_sketch": (
            "If every positive epsilon has a finite L1(P) bracketing cover of "
            "the function class, and finite bracket endpoints satisfy the "
            "needed real-valued endpoint strong law, then the class is a "
            "GlivenkoCantelliClass."
        ),
        "required_primitives": (
            "function class as Index -> sampleSpace -> Real",
            "population L1(P) seminorm or bracket width",
            "finite bracketing cover object with lower/upper endpoint functions",
            "constructor from forall epsilon > 0 finite bracketing number to shrinking finite bracket sequence",
            "endpoint strong-law event for each finite endpoint family",
        ),
        "proof_obligations": (
            "choose a positive scale sequence epsilon_n tending to zero",
            "select finite brackets at each scale without unsafe choice in theorem statement",
            "derive endpoint empirical bounds from finite endpoint SLLN",
            "assemble L1BracketingSequenceRoute and call the compiled bridge",
        ),
        "existing_lean_handoffs": (
            "StatInference.FiniteL1BracketingFamily",
            "StatInference.L1BracketingNumberWitness",
            "StatInference.FiniteL1BracketingNumberAtEveryScale",
            "StatInference.L1BracketingNumberConstructorObligations.toSequenceRoute",
            "StatInference.L1BracketingNumberConstructorObligations.toGlivenkoCantelliClass",
            "StatInference.FiniteBracketEndpointStrongLawAssembly.toConstructorObligations",
            "StatInference.FiniteBracketEndpointStrongLawAssembly.toGlivenkoCantelliClass",
            "StatInference.finite_endpoint_strong_law_eventually_abs_le_real",
            "StatInference.L1BracketingSequenceRoute.toGlivenkoCantelliClass",
        ),
        "benchmark_task_ids": (
            "finite_endpoint_strong_law_eventual_bound_seed",
            "l1_bracketing_sequence_gc_seed",
            "finite_l1_bracketing_number_at_scale_seed",
            "finite_l1_bracketing_every_scale_projection_seed",
            "finite_l1_bracketing_number_constructor_seed",
            "finite_bracket_endpoint_control_constructor_seed",
            "finite_bracket_endpoint_control_gc_seed",
            "vdvw_2_4_1_current_gc_bridge_seed",
            "bracketing_deterministic_bound_seed",
        ),
        "local_lake_validation_hooks": (
            "verify finite_l1_bracketing_number_constructor_seed promotion proof against local Lake",
            "render and verify current bracketing seeds before adding new Lean primitives",
            "run no-sorry scan after any Lean promotion",
        ),
        "axle_validation_hooks": (
            "theorem2sorry on candidate Lean statement before proof work",
            "extract_decls after adding primitive declarations",
            "repair_proofs only after local Lake identifies syntactic breakage",
        ),
        "semantic_risks": (
            "A naive Nat-valued bracketing number can hide missing measurable endpoint and finite-norm assumptions.",
            "Using a global choice of brackets can accidentally assume more than the textbook finite-number hypothesis.",
            "Endpoint SLLN must be tied to the actual bracket endpoints generated by each finite cover.",
        ),
        "promotion_gate": (
            "Add only statement/hole benchmarks first; prove no theorem until non-vacuity and endpoint-SLLN assumptions are explicit.",
        ),
    },
    {
        "candidate_id": "vdvw-2.4.1-full-outer-almost-sure",
        "track": "full_textbook_semantics",
        "status": "blocked_pending_outer_probability_layer",
        "statement_kind": "exact textbook theorem target",
        "target_lean_names": (
            "StatInference.OuterAlmostSureGlivenkoCantelli",
            "StatInference.VdVWMeasurableFunctionClass",
            "StatInference.vdvw_2_4_1_outer_almost_sure",
        ),
        "formal_statement_sketch": (
            "For a class of measurable real-valued functions with finite "
            "L1(P) bracketing number for every epsilon > 0, the outer "
            "supremum norm ||P_n - P||*_F tends to zero outer almost surely."
        ),
        "required_primitives": (
            "outer probability and outer almost-sure convergence",
            "empirical measure P_n for iid samples",
            "supremum seminorm over a function class with measurability policy",
            "measurable function class and endpoint finite-norm requirements",
            "strong law for finitely many endpoint functions in the ambient probability space",
        ),
        "proof_obligations": (
            "formalize the outer supremum GC target",
            "connect finite bracketing numbers to finite endpoint families",
            "prove upper and lower empirical-process inequalities from brackets",
            "take decreasing epsilon_m to force limsup equal zero",
        ),
        "existing_lean_handoffs": (
            "StatInference.GlivenkoCantelliClass",
            "StatInference.L1BracketingSequenceRoute.toGlivenkoCantelliClass",
        ),
        "benchmark_task_ids": (
            "glivenko_cantelli_statement_seed",
            "bracketing_deterministic_bound_seed",
            "finite_endpoint_strong_law_eventual_bound_seed",
        ),
        "local_lake_validation_hooks": (
            "keep this as a source-linked theorem card until outer probability APIs exist",
            "validate any exact-theorem Lean declaration with lake build and forbidden-shortcut scan",
        ),
        "axle_validation_hooks": (
            "check exact theorem statement candidate after local syntax is stable",
            "disprove candidate only for vacuity/sanity checks on deliberately overstrong variants",
        ),
        "semantic_risks": (
            "Current GlivenkoCantelliClass is an inner deterministic radius interface, not the outer-almost-sure textbook conclusion.",
            "Omitting outer probability would change the theorem.",
            "Omitting measurability assumptions can make the Lean statement weaker or vacuous.",
        ),
        "promotion_gate": (
            "Do not promote as exact theorem until outer probability, empirical measure, and measurable-class primitives compile.",
        ),
    },
)

DEFAULT_VDVW_VC_DONSKER_SOURCE_ANCHORS = (
    {
        "anchor_id": "vdvw-2.5.2-uniform-entropy-donsker",
        "label": "Theorem 2.5.2",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 1106,
        "line_end": 1118,
        "purpose": "uniform entropy condition to P-Donsker theorem target",
    },
    {
        "anchor_id": "vdvw-2.5.6-bracketing-donsker",
        "label": "Theorem 2.5.6",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 1204,
        "line_end": 1220,
        "purpose": "bracketing entropy integral to P-Donsker theorem target",
    },
    {
        "anchor_id": "vdvw-2.6.4-vc-set-covering",
        "label": "Theorem 2.6.4",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 1378,
        "line_end": 1383,
        "purpose": "VC set class polynomial covering-number bound",
    },
    {
        "anchor_id": "vdvw-2.6.7-vc-subgraph-covering",
        "label": "Theorem 2.6.7",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 1490,
        "line_end": 1497,
        "purpose": "VC-subgraph envelope-scaled covering-number bound",
    },
    {
        "anchor_id": "vdvw-2.6.8-vc-subgraph-donsker",
        "label": "Theorem 2.6.8",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 1520,
        "line_end": 1524,
        "purpose": "pointwise separable pre-Gaussian VC class with weak envelope tail is P-Donsker",
    },
)

DEFAULT_VDVW_VC_DONSKER_PROOF_OBLIGATIONS = (
    {
        "obligation_id": "vdvw-2.6.4-vc-set-entropy-obligations",
        "source_label": "Theorem 2.6.4",
        "track": "vc_set_entropy",
        "status": "blocked_pending_vc_primitives",
        "target_lean_names": (
            "StatInference.VCSetClassSpec",
            "StatInference.VCSetCoveringNumberBound",
            "StatInference.vdvw_2_6_4_vc_set_covering_bound",
        ),
        "formal_goal": (
            "Construct a polynomial Lr(Q) covering-number bound for VC set "
            "classes from shattering and Sauer-style growth control."
        ),
        "required_primitives": (
            "set-class shattering predicate",
            "VC index or VC dimension for measurable set classes",
            "growth function Delta_n(C, x_1, ..., x_n)",
            "Sauer-Shelah growth bound",
            "Lr(Q) covering number for indicator set classes",
        ),
        "proof_obligations": (
            "reduce arbitrary probability measures to empirical-type measures",
            "translate set symmetric-difference distance into indicator Lr distance",
            "apply growth-function bound to construct a finite cover",
            "track universal constants without hiding theorem assumptions",
        ),
        "current_lean_handoffs": (
            "StatInference.VCSubgraphProofObligations",
            "StatInference.VCSubgraphSpec",
            "StatInference.VCSubgraphGCRoute",
        ),
        "benchmark_task_ids": (
            "vc_deviation_certificate_gc_seed",
            "vc_subgraph_route_certificate_seed",
            "trivial_vc_subgraph_gc_non_vacuity_seed",
        ),
        "validation_hooks": (
            "render and verify vc_deviation_certificate_gc_seed",
            "extract_decls on StatInference/EmpiricalProcess/VCSubgraph.lean",
            "run local no-sorry scan before any Lean promotion",
        ),
        "semantic_risks": (
            "Current VCSubgraphSpec is metadata and does not prove shattering or Sauer bounds.",
            "Set-class VC entropy must stay separate from real-valued VC-subgraph entropy.",
        ),
        "promotion_gate": "Add theorem-hole signatures first; do not claim a VC entropy theorem until shattering and covering-number primitives compile.",
    },
    {
        "obligation_id": "vdvw-2.6.7-vc-subgraph-entropy-obligations",
        "source_label": "Theorem 2.6.7",
        "track": "vc_subgraph_entropy",
        "status": "blocked_pending_subgraph_envelope_primitives",
        "target_lean_names": (
            "StatInference.VCSubgraphEntropyObligations",
            "StatInference.VCSubgraphEnvelopeCoveringBound",
            "StatInference.vdvw_2_6_7_vc_subgraph_covering_bound",
        ),
        "formal_goal": (
            "Lift the VC set-class covering bound to real-valued VC-subgraph "
            "classes with measurable envelope and envelope-scaled Lr(Q) radius."
        ),
        "required_primitives": (
            "subgraph set associated with a real-valued function",
            "measurable envelope and positive Lr(Q) envelope norm",
            "product measure with Lebesgue measure on the real line",
            "Fubini identity connecting Q|f-g| and subgraph symmetric difference",
            "envelope-weighted probability renormalization",
        ),
        "proof_obligations": (
            "prove subgraphs form a VC set class with the stated VC index",
            "derive the L1(Q) covering bound through product-measure geometry",
            "lift from r = 1 to general r >= 1 through envelope weighting",
            "preserve envelope measurability and nonzero-norm side conditions",
        ),
        "current_lean_handoffs": (
            "StatInference.VCSubgraphProofObligations",
            "StatInference.VCDeviationCertificate",
            "StatInference.VCSubgraphGCRoute.toVCDeviationCertificate",
        ),
        "benchmark_task_ids": (
            "vc_subgraph_route_certificate_seed",
            "vc_deviation_certificate_gc_seed",
        ),
        "validation_hooks": (
            "render and verify vc_subgraph_route_certificate_seed",
            "check that VCDeviationCertificate remains proof-carrying",
            "AXLE check only after local Lake accepts candidate signatures",
        ),
        "semantic_risks": (
            "Dropping the measurable-envelope condition changes the theorem.",
            "A generic VCSubgraphGCRoute cannot be reused as evidence for the entropy theorem.",
        ),
        "promotion_gate": "Promote only after set-class VC entropy and subgraph/envelope primitives are explicit.",
    },
    {
        "obligation_id": "vdvw-2.5.2-uniform-entropy-donsker-obligations",
        "source_label": "Theorem 2.5.2",
        "track": "uniform_entropy_donsker",
        "status": "blocked_pending_donsker_semantics",
        "target_lean_names": (
            "StatInference.UniformEntropyDonskerObligations",
            "StatInference.vdvw_2_5_2_uniform_entropy_donsker",
        ),
        "formal_goal": (
            "Construct P-Donsker weak convergence from the uniform entropy "
            "condition, measurability of local difference classes, and a "
            "square-integrable envelope."
        ),
        "required_primitives": (
            "uniform entropy integral over finitely discrete Q",
            "L2(P) semimetric and local class F_delta",
            "outer measurability for F_delta and F_infty^2",
            "empirical process as random element in ell-infinity(F)",
            "tight Brownian bridge or pre-Gaussian target process",
        ),
        "proof_obligations": (
            "formalize symmetrization and Rademacher sub-Gaussian process bound",
            "connect maximal inequality to asymptotic equicontinuity",
            "prove finite-dimensional convergence or consume a CLT field",
            "assemble weak convergence and tightness into DonskerSpec",
        ),
        "current_lean_handoffs": (
            "StatInference.DonskerSpec",
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerAsymptoticNormalityRoute",
        ),
        "benchmark_task_ids": (
            "donsker_statement_seed",
            "donsker_bridge_gc_projection_seed",
            "donsker_bridge_estimator_clt_seed",
        ),
        "validation_hooks": (
            "render and verify donsker_statement_seed",
            "keep DonskerSpec as consumed weak-convergence evidence until primitives exist",
            "avoid converting GC-only certificates into Donsker evidence",
        ),
        "semantic_risks": (
            "Donsker is strictly stronger than GC and cannot be inferred from current GC certificates.",
            "Current DonskerSpec stores a weak-convergence statement but does not construct it from entropy.",
        ),
        "promotion_gate": "Keep as proof-obligation card until empirical-process weak convergence and tightness APIs exist.",
    },
    {
        "obligation_id": "vdvw-2.5.6-bracketing-donsker-obligations",
        "source_label": "Theorem 2.5.6",
        "track": "bracketing_donsker",
        "status": "blocked_pending_entropy_integral_primitives",
        "target_lean_names": (
            "StatInference.BracketingDonskerObligations",
            "StatInference.vdvw_2_5_6_bracketing_entropy_donsker",
        ),
        "formal_goal": (
            "Construct P-Donsker weak convergence from finite L2 and weak-L2 "
            "bracketing/covering entropy integrals plus weak second moment."
        ),
        "required_primitives": (
            "L2(P) bracketing/covering entropy integral",
            "L2,infty(P) weak bracketing entropy integral",
            "weak second-moment envelope condition",
            "partition-chain construction over the function class",
            "Donsker weak convergence target in function space",
        ),
        "proof_obligations": (
            "construct finite partitions with summable entropy weights",
            "prove chaining bounds for empirical-process increments",
            "handle truncation through weak second-moment envelope control",
            "produce DonskerBridgeCertificate only after weak convergence is constructed",
        ),
        "current_lean_handoffs": (
            "StatInference.BracketingNumberSpec",
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerAsymptoticNormalityRoute.asymptoticNormal",
        ),
        "benchmark_task_ids": (
            "bracketing_certificate_gc_seed",
            "donsker_asymptotic_normality_handoff_seed",
            "trivial_donsker_asymptotic_normality_seed",
        ),
        "validation_hooks": (
            "render and verify bracketing_certificate_gc_seed",
            "render and verify donsker_asymptotic_normality_handoff_seed",
            "do not reuse bracketing GC certificate as Donsker proof",
        ),
        "semantic_risks": (
            "Bracketing GC infrastructure is insufficient for bracketing Donsker.",
            "Entropy-integral finiteness and weak second moment are not encoded in BracketingNumberSpec.",
        ),
        "promotion_gate": "Promote only after entropy-integral APIs and Donsker weak-convergence target are explicit.",
    },
    {
        "obligation_id": "vdvw-2.6.8-vc-subgraph-donsker-obligations",
        "source_label": "Theorem 2.6.8",
        "track": "vc_subgraph_donsker",
        "status": "blocked_pending_pregaussian_tail_layer",
        "target_lean_names": (
            "StatInference.VCSubgraphDonskerObligations",
            "StatInference.vdvw_2_6_8_vc_subgraph_donsker",
        ),
        "formal_goal": (
            "Construct P-Donsker for pointwise separable, P-pre-Gaussian "
            "VC-subgraph classes under a weak second-moment envelope tail."
        ),
        "required_primitives": (
            "pointwise separability",
            "P-pre-Gaussian process indexed by a function class",
            "weak second-moment envelope tail P*(F > x) = o(x^-2)",
            "bridge from VC entropy plus pre-Gaussianity to asymptotic tightness",
            "Donsker constructor from finite-dimensional convergence and tightness",
        ),
        "proof_obligations": (
            "reuse VC-subgraph entropy only as an input obligation",
            "separate finite-second-moment shortcut through Theorem 2.5.2 from weak-tail refinement",
            "encode Alexander refinement as a theorem card until proof infrastructure exists",
            "connect finished Donsker proof to estimator normality only through DonskerAsymptoticNormalityRoute",
        ),
        "current_lean_handoffs": (
            "StatInference.VCSubgraphGCRoute",
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerAsymptoticNormalityRoute",
        ),
        "benchmark_task_ids": (
            "vc_subgraph_route_certificate_seed",
            "donsker_bridge_estimator_clt_seed",
            "donsker_asymptotic_normality_handoff_seed",
        ),
        "validation_hooks": (
            "render and verify vc_subgraph_route_certificate_seed",
            "render and verify donsker_bridge_estimator_clt_seed",
            "check that Donsker handoff remains separate from VC GC route",
        ),
        "semantic_risks": (
            "The theorem has stronger assumptions than VC-subgraph GC.",
            "Pre-Gaussianity and weak-tail assumptions cannot be replaced by current VCSubgraphGCRoute metadata.",
        ),
        "promotion_gate": "Keep as theorem card until pre-Gaussian, weak-tail, and Donsker semantics compile.",
    },
)

DEFAULT_VDVW_PRIMITIVE_SEMANTICS_SOURCE_ANCHORS = (
    {
        "anchor_id": "vdvw-gc-definition",
        "label": "Glivenko-Cantelli class definition",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_1-100.md",
        "line_start": 1834,
        "line_end": 1834,
        "purpose": "outer-probability or outer-almost-sure uniform law target",
    },
    {
        "anchor_id": "vdvw-2.1.6-bracketing-number",
        "label": "Definition 2.1.6",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_1-100.md",
        "line_start": 1895,
        "line_end": 1895,
        "purpose": "brackets, epsilon-brackets, and bracketing-number semantics",
    },
    {
        "anchor_id": "vdvw-2.4.1-finite-l1-bracketing-gc",
        "label": "Theorem 2.4.1",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 970,
        "line_end": 985,
        "purpose": "finite L1(P) bracketing to Glivenko-Cantelli proof route",
    },
    {
        "anchor_id": "vdvw-2.5.2-uniform-entropy-donsker",
        "label": "Theorem 2.5.2",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 1106,
        "line_end": 1118,
        "purpose": "uniform entropy Donsker target requiring primitive weak-convergence semantics",
    },
    {
        "anchor_id": "vdvw-2.5.6-bracketing-donsker",
        "label": "Theorem 2.5.6",
        "segment": "Vaart 1996 Weak Convergence and Emperical Process_101-200.md",
        "line_start": 1204,
        "line_end": 1220,
        "purpose": "bracketing entropy-integral Donsker target requiring primitive entropy-integral semantics",
    },
)

DEFAULT_VDVW_PRIMITIVE_EMPIRICAL_SEMANTICS = (
    {
        "primitive_id": "empirical-sample-average",
        "layer": "empirical_sample",
        "status": "design_ready_measure_backed_endpoint_semantics",
        "source_anchor_ids": (
            "vdvw-gc-definition",
            "vdvw-2.4.1-finite-l1-bracketing-gc",
        ),
        "target_lean_module": "StatInference.EmpiricalProcess.VdVW241",
        "target_lean_signatures": (
            "noncomputable def bracketEndpointEmpiricalAverage (sample : SampleAt Observation sampleSize) (endpoint : Bracket -> Observation -> ℝ) (bracket : Bracket) : ℝ",
            "noncomputable def bracketEndpointEmpiricalSequence (samples : ∀ sampleSize, SampleAt Observation sampleSize) (endpoint : Bracket -> Observation -> ℝ) : ℕ -> Bracket -> ℝ",
            "noncomputable def bracketEndpointPopulationIntegral (populationMeasure : Measure Observation) (endpoint : Bracket -> Observation -> ℝ) (bracket : Bracket) : ℝ",
            "noncomputable def bracketEndpointEmpiricalMeasureSequence (empiricalMeasure : ℕ -> Measure Observation) (endpoint : Bracket -> Observation -> ℝ) : ℕ -> Bracket -> ℝ",
            "structure FiniteBracketSampleAverageSemantics (indexClass : Set Index) (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)",
            "structure FiniteBracketEmpiricalMeasureSemantics (indexClass : Set Index) (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)",
        ),
        "current_lean_handoffs": (
            "StatInference.empiricalAverage",
            "StatInference.bracketEndpointEmpiricalAverage",
            "StatInference.bracketEndpointEmpiricalSequence",
            "StatInference.bracketEndpointPopulationIntegral",
            "StatInference.bracketEndpointEmpiricalMeasureSequence",
            "StatInference.FiniteBracketSampleAverageSemantics.toEndpointStrongLawAssembly",
            "StatInference.FiniteBracketSampleAverageSemantics.toConstructorObligations",
            "StatInference.FiniteBracketSampleAverageSemantics.toGlivenkoCantelliClass",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toEndpointStrongLawAssembly",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toConstructorObligations",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toGlivenkoCantelliClass",
            "StatInference.endpoint_strong_law_ae_real",
            "StatInference.finite_endpoint_strong_law_eventually_abs_le_real",
            "StatInference.EmpiricalDeviationSequenceOn",
        ),
        "theorem_card_gaps": (
            "empirical measure P_n as sample averages of real-valued functions",
            "common sample object shared by all bracket endpoints",
            "population functional P f tied to the same function class",
        ),
        "existing_benchmark_task_ids": (
            "finite_endpoint_strong_law_eventual_bound_seed",
            "bracketing_deterministic_bound_seed",
            "finite_bracket_sample_average_assembly_seed",
            "finite_bracket_sample_average_constructor_seed",
            "finite_bracket_sample_average_gc_seed",
            "finite_bracket_empirical_measure_assembly_seed",
            "finite_bracket_empirical_measure_constructor_seed",
            "finite_bracket_empirical_measure_gc_seed",
        ),
        "planned_theorem_hole_seed_ids": (
            "empirical_measure_endpoint_signature_seed",
            "empirical_process_outer_deviation_endpoint_seed",
        ),
        "validation_hooks": (
            "keep sample-average endpoint semantics separate from empirical-measure probability semantics",
            "measure-backed endpoint semantics must still be tied to concrete iid empirical measures before exact outer-GC theorem work",
            "run lake build and no-sorry scan after promotion",
        ),
        "semantic_risks": (
            "Do not treat a sequence of arbitrary empirical risks as an iid empirical measure.",
            "Do not hide sample-size zero denominator behavior in empirical averages.",
        ),
        "promotion_gate": "Promote only after sample-average and measure-backed endpoint notation compile and preserve existing endpoint SLLN benchmarks.",
    },
    {
        "primitive_id": "outer-uniform-convergence",
        "layer": "outer_convergence",
        "status": "design_ready_outer_signature_semantics",
        "source_anchor_ids": (
            "vdvw-gc-definition",
            "vdvw-2.4.1-finite-l1-bracketing-gc",
        ),
        "target_lean_module": "StatInference.EmpiricalProcess.Outer",
        "target_lean_signatures": (
            "structure OuterProbabilitySpace (Ω : Type*) [MeasurableSpace Ω] where outerProb : Set Ω -> ℝ",
            "def OuterTendstoInProbability (outerProb : Set Ω -> ℝ) (X : ℕ -> Ω -> ℝ) (limit : ℝ) : Prop",
            "def OuterAlmostSureTendsto (outerProb : Set Ω -> ℝ) (X : ℕ -> Ω -> ℝ) (limit : ℝ) : Prop",
            "def OuterSupremumDeviation (F : Set (Ω -> ℝ)) (empirical population : (Ω -> ℝ) -> ℝ) : ℝ",
            "structure OuterGlivenkoCantelliClass (outer : OuterProbabilitySpace Ω) (indexClass : Set Index) (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Ω -> Index -> ℝ)",
        ),
        "current_lean_handoffs": (
            "StatInference.OuterProbabilitySpace",
            "StatInference.OuterProbabilitySpace.event_mono",
            "StatInference.OuterTendstoInProbability",
            "StatInference.OuterAlmostSureTendsto",
            "StatInference.OuterSupremumDeviation",
            "StatInference.OuterGlivenkoCantelliClass.tendstoInProbability",
            "StatInference.OuterGlivenkoCantelliClass.almostSureTendsto",
            "StatInference.GlivenkoCantelliClass",
            "StatInference.EmpiricalDeviationSequenceOn",
        ),
        "theorem_card_gaps": (
            "outer probability P* and outer almost-sure convergence",
            "outer supremum norm ||P_n - P||*_F",
            "measurability policy for nonmeasurable suprema over function classes",
        ),
        "existing_benchmark_task_ids": (
            "glivenko_cantelli_statement_seed",
            "l1_bracketing_sequence_gc_seed",
            "outer_probability_space_monotone_seed",
            "outer_gc_projection_seed",
        ),
        "planned_theorem_hole_seed_ids": (
            "outer_supremum_deviation_signature_seed",
            "outer_gc_to_current_gc_bridge_seed",
        ),
        "validation_hooks": (
            "keep exact VdV&W Theorem 2.4.1 blocked until this module exists",
            "check that current deterministic GC interface is not labeled outer almost-sure",
            "use AXLE check only after local Lake accepts statement candidates",
        ),
        "semantic_risks": (
            "Replacing outer convergence by ordinary convergence changes the textbook theorem.",
            "A deterministic radius sequence is not itself an outer-probability statement.",
        ),
        "promotion_gate": "Promote only as semantics signatures until outer measurability and non-vacuity examples are available.",
    },
    {
        "primitive_id": "measurable-function-class-l1",
        "layer": "function_class_l1",
        "status": "design_ready_for_lean_signature",
        "source_anchor_ids": (
            "vdvw-2.1.6-bracketing-number",
            "vdvw-2.4.1-finite-l1-bracketing-gc",
        ),
        "target_lean_module": "StatInference.EmpiricalProcess.L1Semantics",
        "target_lean_signatures": (
            "structure VdVWFunctionClass (Ω : Type*) [MeasurableSpace Ω] where carrier : Set (Ω -> ℝ)",
            "def L1Width (PIntegral : (Ω -> ℝ) -> ℝ) (lower upper : Ω -> ℝ) : ℝ",
            "structure L1Bracket (PIntegral : (Ω -> ℝ) -> ℝ) (epsilon : ℝ) where lower upper : Ω -> ℝ",
        ),
        "current_lean_handoffs": (
            "StatInference.FiniteL1BracketingFamily",
            "StatInference.empiricalDeviationBoundOn_of_bracket_endpoint_bounds",
        ),
        "theorem_card_gaps": (
            "measurable real-valued function class",
            "finite L1(P)-norm bracket endpoints",
            "pointwise lower <= f <= upper relation",
        ),
        "existing_benchmark_task_ids": (
            "bracketing_deterministic_bound_seed",
            "trivial_bracketing_gc_non_vacuity_seed",
        ),
        "planned_theorem_hole_seed_ids": (
            "l1_bracket_contains_function_seed",
            "l1_width_to_population_width_seed",
        ),
        "validation_hooks": (
            "compile signatures before linking to bracketing-number constructors",
            "prove one-point non-vacuity before theorem promotion",
        ),
        "semantic_risks": (
            "Endpoint finite-norm and measurability assumptions must remain explicit.",
            "The bracket endpoints need not belong to the function class.",
        ),
        "promotion_gate": "Promote only with explicit endpoint measurability and finite-norm fields or proof-carrying assumptions.",
    },
    {
        "primitive_id": "primitive-l1-bracketing-number",
        "layer": "bracketing_number",
        "status": "design_ready_compiled_constructor_signature",
        "source_anchor_ids": (
            "vdvw-2.1.6-bracketing-number",
            "vdvw-2.4.1-finite-l1-bracketing-gc",
        ),
        "target_lean_module": "StatInference.EmpiricalProcess.L1BracketingNumber",
        "target_lean_signatures": (
            "structure L1BracketingNumberWitness (indexClass : Set Index) (populationRisk : Index -> ℝ) (scale : ℝ)",
            "def L1BracketingNumberFiniteAt (indexClass : Set Index) (populationRisk : Index -> ℝ) (scale : ℝ) : Prop",
            "structure FiniteL1BracketingNumberAtEveryScale (indexClass : Set Index) (populationRisk : Index -> ℝ)",
            "structure L1BracketingNumberConstructorObligations (indexClass : Set Index) (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)",
        ),
        "current_lean_handoffs": (
            "StatInference.FiniteL1BracketingFamily",
            "StatInference.L1BracketingSequenceRoute",
            "StatInference.L1BracketingSequenceRoute.toGlivenkoCantelliClass",
            "StatInference.L1BracketingNumberWitness",
            "StatInference.FiniteL1BracketingNumberAtEveryScale",
            "StatInference.L1BracketingNumberConstructorObligations.toSequenceRoute",
            "StatInference.L1BracketingNumberConstructorObligations.toGlivenkoCantelliClass",
        ),
        "theorem_card_gaps": (
            "constructor from varying finite bracketing-number witnesses into a common finite Bracket type when the route requires one fixed bracket index type",
            "scale sequence epsilon_m descending to zero",
            "endpoint strong-law events for selected lower and upper bracket endpoints",
        ),
        "existing_benchmark_task_ids": (
            "l1_bracketing_sequence_gc_seed",
            "finite_l1_bracketing_number_at_scale_seed",
            "finite_l1_bracketing_every_scale_projection_seed",
            "finite_l1_bracketing_number_constructor_seed",
            "finite_endpoint_strong_law_eventual_bound_seed",
        ),
        "planned_theorem_hole_seed_ids": (
            "finite_l1_bracketing_every_scale_to_sequence_route_seed",
        ),
        "validation_hooks": (
            "do not introduce a Nat-valued bracketing number without cover data",
            "constructor theorem-hole seeds must have a promoted no-placeholder proof target before library curation claims success",
            "run benchmark determinism after adding seeds",
        ),
        "semantic_risks": (
            "A bare finite cardinality statement can hide the actual covering functions.",
            "Unsafe choice of covers can accidentally strengthen the textbook assumption.",
        ),
        "promotion_gate": "Promote after signatures can construct an explicit finite cover object for any positive scale.",
    },
    {
        "primitive_id": "finite-bracketing-gc-assembly",
        "layer": "gc_constructor",
        "status": "design_ready_current_gc_endpoint_assembly",
        "source_anchor_ids": (
            "vdvw-2.4.1-finite-l1-bracketing-gc",
        ),
        "target_lean_module": "StatInference.EmpiricalProcess.VdVW241",
        "target_lean_signatures": (
            "structure FiniteBracketEndpointStrongLawAssembly (indexClass : Set Index) (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)",
            "def FiniteBracketEndpointStrongLawAssembly.toConstructorObligations : L1BracketingNumberConstructorObligations indexClass populationRisk empiricalRisk",
            "def FiniteBracketEndpointStrongLawAssembly.toGlivenkoCantelliClass : GlivenkoCantelliClass indexClass populationRisk empiricalRisk",
            "structure FiniteBracketSampleAverageSemantics (indexClass : Set Index) (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)",
            "def FiniteBracketSampleAverageSemantics.toEndpointStrongLawAssembly : FiniteBracketEndpointStrongLawAssembly indexClass populationRisk empiricalRisk",
            "def FiniteBracketSampleAverageSemantics.toGlivenkoCantelliClass : GlivenkoCantelliClass indexClass populationRisk empiricalRisk",
            "structure FiniteBracketEmpiricalMeasureSemantics (indexClass : Set Index) (populationRisk : Index -> ℝ) (empiricalRisk : ℕ -> Index -> ℝ)",
            "def FiniteBracketEmpiricalMeasureSemantics.toEndpointStrongLawAssembly : FiniteBracketEndpointStrongLawAssembly indexClass populationRisk empiricalRisk",
            "def FiniteBracketEmpiricalMeasureSemantics.toGlivenkoCantelliClass : GlivenkoCantelliClass indexClass populationRisk empiricalRisk",
        ),
        "current_lean_handoffs": (
            "StatInference.empiricalDeviationBoundOn_of_bracket_endpoint_bounds",
            "StatInference.finite_endpoint_strong_law_eventually_abs_le_real",
            "StatInference.L1BracketingSequenceRoute.toGlivenkoCantelliClass",
            "StatInference.FiniteBracketEndpointStrongLawAssembly.toConstructorObligations",
            "StatInference.FiniteBracketEndpointStrongLawAssembly.toGlivenkoCantelliClass",
            "StatInference.FiniteBracketSampleAverageSemantics.toEndpointStrongLawAssembly",
            "StatInference.FiniteBracketSampleAverageSemantics.toConstructorObligations",
            "StatInference.FiniteBracketSampleAverageSemantics.toGlivenkoCantelliClass",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toEndpointStrongLawAssembly",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toConstructorObligations",
            "StatInference.FiniteBracketEmpiricalMeasureSemantics.toGlivenkoCantelliClass",
        ),
        "theorem_card_gaps": (
            "limsup epsilon_m to zero argument under outer almost-sure semantics",
            "empirical measure P_n as a probability measure rather than only sample averages",
            "outer probability and outer almost-sure GC target",
        ),
        "existing_benchmark_task_ids": (
            "bracketing_deterministic_bound_seed",
            "finite_endpoint_strong_law_eventual_bound_seed",
            "l1_bracketing_sequence_gc_seed",
            "finite_bracket_endpoint_control_constructor_seed",
            "finite_bracket_endpoint_control_gc_seed",
            "finite_bracket_sample_average_assembly_seed",
            "finite_bracket_sample_average_constructor_seed",
            "finite_bracket_sample_average_gc_seed",
            "finite_bracket_empirical_measure_assembly_seed",
            "finite_bracket_empirical_measure_constructor_seed",
            "finite_bracket_empirical_measure_gc_seed",
            "vdvw_2_4_1_current_gc_bridge_seed",
        ),
        "planned_theorem_hole_seed_ids": (
            "vdvw_2_4_1_outer_almost_sure_statement_seed",
        ),
        "validation_hooks": (
            "keep current-GC bridge separate from the exact outer almost-sure theorem",
            "require local Lake, no-sorry scan, and source-anchor audit before report promotion",
        ),
        "semantic_risks": (
            "The compiled current-GC bridge is weaker than the exact outer almost-sure statement.",
            "Measure-backed endpoint semantics still need concrete iid empirical-measure construction and outer convergence events.",
        ),
        "promotion_gate": "Promote first as current-GC bridge; exact VdVW 2.4.1 waits for outer-convergence semantics.",
    },
    {
        "primitive_id": "donsker-weak-convergence-target",
        "layer": "donsker_semantics",
        "status": "blocked_pending_function_space_weak_convergence",
        "source_anchor_ids": (
            "vdvw-2.5.2-uniform-entropy-donsker",
            "vdvw-2.5.6-bracketing-donsker",
        ),
        "target_lean_module": "StatInference.EmpiricalProcess.DonskerSemantics",
        "target_lean_signatures": (
            "structure EmpiricalProcessRandomElement (F : VdVWFunctionClass Ω) where path : ℕ -> Ω -> (F.carrier -> ℝ)",
            "structure PreGaussianLimit (F : VdVWFunctionClass Ω) where covariance_statement : Prop",
            "def DonskerWeakConvergence (process : EmpiricalProcessRandomElement F) (limit : PreGaussianLimit F) : Prop",
        ),
        "current_lean_handoffs": (
            "StatInference.DonskerSpec",
            "StatInference.DonskerBridgeCertificate",
            "StatInference.DonskerAsymptoticNormalityRoute",
        ),
        "theorem_card_gaps": (
            "empirical process as random element in ell-infinity of a function class",
            "pre-Gaussian or Brownian-bridge limit process",
            "tightness and finite-dimensional convergence split",
        ),
        "existing_benchmark_task_ids": (
            "donsker_statement_seed",
            "donsker_bridge_estimator_clt_seed",
            "donsker_asymptotic_normality_handoff_seed",
        ),
        "planned_theorem_hole_seed_ids": (
            "donsker_weak_convergence_signature_seed",
            "donsker_entropy_constructor_statement_seed",
        ),
        "validation_hooks": (
            "keep DonskerSpec proof-carrying until this semantic layer compiles",
            "never promote GC certificates to Donsker evidence",
        ),
        "semantic_risks": (
            "Donsker semantics require weak convergence and tightness, not just uniform laws.",
            "Pre-Gaussianity and separability assumptions must remain visible.",
        ),
        "promotion_gate": "Promote only after function-space weak-convergence target and non-vacuity examples exist.",
    },
)

DEFAULT_EXTERNAL_BASELINES = (
    {
        "baseline_id": "seed-registry",
        "display_name": "Checked-in seed registry proof render",
        "runner_type": "local_oracle",
        "status": "ready",
        "requires": (),
        "command_template": (
            "statlean materialize-benchmark-attempts --benchmarks {benchmarks} --output {attempts} "
            "--agent-key seed-registry && statlean verify-attempts --attempts {attempts} "
            "--output {reports} --benchmarks {benchmarks}"
        ),
    },
    {
        "baseline_id": "reprover-byt5",
        "display_name": "LeanDojo/ReProver retrieval-augmented tactic model",
        "runner_type": "external_model",
        "status": "requires_model_setup",
        "requires": ("LeanDojo/ReProver runtime", "model checkpoint", "premise index adapter"),
        "command_template": "external-runner reprover --benchmarks {benchmarks} --split {split} --output {attempts}",
    },
    {
        "baseline_id": "deepseek-prover-v2-7b",
        "display_name": "DeepSeek-Prover-V2 7B whole-proof generator",
        "runner_type": "external_model",
        "status": "requires_model_setup",
        "requires": ("model weights or endpoint", "GPU or hosted inference", "whole-proof adapter"),
        "command_template": "external-runner deepseek-prover-v2 --benchmarks {benchmarks} --split {split} --output {attempts}",
    },
    {
        "baseline_id": "kimina-prover-rl-1.7b",
        "display_name": "Kimina-Prover RL 1.7B whole-proof generator",
        "runner_type": "external_model",
        "status": "requires_model_setup",
        "requires": ("model weights or endpoint", "Kimina Lean Server optional", "whole-proof adapter"),
        "command_template": "external-runner kimina-prover --benchmarks {benchmarks} --split {split} --output {attempts}",
    },
    {
        "baseline_id": "general-llm-codex",
        "display_name": "General coding-agent Lean proof baseline",
        "runner_type": "agentic_llm",
        "status": "requires_harness",
        "requires": ("agent harness", "timeout policy", "attempt capture adapter"),
        "command_template": "external-runner codex --benchmarks {benchmarks} --split {split} --output {attempts}",
    },
)

DEFAULT_REPRODUCIBILITY_COMMANDS = (
    {
        "name": "python_tests",
        "command": "PYTHONPATH=src .venv/bin/python -m pytest",
        "purpose": "Run the complete Python test suite.",
    },
    {
        "name": "smoke",
        "command": "PYTHON=.venv/bin/python bash scripts/smoke.sh",
        "purpose": "Run deterministic benchmark, premise-index, manifest, and blueprint smoke checks.",
    },
    {
        "name": "lean_build",
        "command": "lake build",
        "purpose": "Compile the Lean StatInference library and benchmark modules.",
    },
    {
        "name": "blueprint_status",
        "command": "PYTHONPATH=src .venv/bin/python -m statlean_agent.cli blueprint-status --blueprint config/statlean_blueprint.json",
        "purpose": "Confirm the executable build blueprint status.",
    },
    {
        "name": "forbidden_lean_shortcuts",
        "command": "rg -n \"\\b(sorry|admit|unsafe)\\b|^\\s*axiom\\b\" StatInference -g '*.lean'",
        "purpose": "Fail if promoted Lean sources contain forbidden proof shortcuts.",
    },
)


def evaluate_attempts(
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    allowed_placeholders_by_task: Mapping[str, Iterable[str]] | None = None,
) -> EvalReport:
    """Aggregate proof-attempt metrics."""

    if len(attempts) != len(reports):
        raise ValueError("attempts and reports must have the same length")

    allowed_by_task = allowed_placeholders_by_task or {}
    total = len(attempts)
    status_counts = _empty_status_counts()
    diagnostics: list[str] = []
    reward_breakdowns = []

    for attempt, report in zip(attempts, reports, strict=True):
        if attempt.task_id != report.task_id:
            diagnostics.append(
                f"{attempt.task_id}: paired with report for `{report.task_id}`; metrics use the report status"
            )

        allowed_placeholders = tuple(allowed_by_task.get(attempt.task_id, ()))
        effective_status, reward_breakdown, _, _ = _evaluate_attempt_record(
            attempt,
            report,
            allowed_placeholders=allowed_placeholders,
            diagnostics=diagnostics,
        )
        status_counts[effective_status.value] += 1
        reward_breakdowns.append(reward_breakdown)

    reward_total = aggregate_reward_breakdowns(reward_breakdowns)
    average_reward = reward_total.total / total if total else 0.0
    average_reward_components = {
        key: value / total for key, value in reward_total.components.items()
    } if total else {}
    accepted = status_counts[VerificationStatus.ACCEPTED.value]
    rejected = status_counts[VerificationStatus.REJECTED.value]
    timeout = status_counts[VerificationStatus.TIMEOUT.value]
    error = status_counts[VerificationStatus.ERROR.value]
    pass_rate = accepted / total if total else 0.0

    return EvalReport(
        total_attempts=total,
        accepted=accepted,
        rejected=rejected,
        timeout=timeout,
        error=error,
        average_reward=average_reward,
        pass_rate=pass_rate,
        status_counts=status_counts,
        reward_totals=reward_total.components,
        average_reward_components=average_reward_components,
        diagnostics=tuple(diagnostics),
    )


def summarize_benchmark_attempts(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    allowed_placeholders_by_task: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, object]:
    """Summarize benchmark attempts by split, domain tag, and task type.

    Domain-tag rows count each attempt once per tag, so their totals can exceed
    the global attempt count for multi-domain benchmark tasks.
    """

    if len(attempts) != len(reports):
        raise ValueError("attempts and reports must have the same length")

    task_by_id = _task_index(tasks)
    allowed_by_task = _allowed_placeholders_by_task(tasks)
    if allowed_placeholders_by_task is not None:
        allowed_by_task.update({
            task_id: tuple(tokens)
            for task_id, tokens in allowed_placeholders_by_task.items()
        })
    total = _SummaryBucket()
    by_phase: dict[str, _SummaryBucket] = {}
    by_split: dict[str, _SummaryBucket] = {}
    by_domain: dict[str, _SummaryBucket] = {}
    by_task_type: dict[str, _SummaryBucket] = {}

    for attempt, report in zip(attempts, reports, strict=True):
        task = task_by_id.get(attempt.task_id)
        if task is None:
            raise ValueError(f"unknown benchmark task id: {attempt.task_id}")

        allowed_placeholders = tuple(allowed_by_task.get(attempt.task_id, ()))
        effective_status, reward_breakdown, first_error, violations = _evaluate_attempt_record(
            attempt,
            report,
            allowed_placeholders=allowed_placeholders,
        )
        failure_category = _failure_category(
            effective_status,
            first_error=first_error,
            diagnostics=report.diagnostics,
            violations=violations,
        )

        split = _enum_value(task.split)
        task_type = _enum_value(task.task_type)
        domains = tuple(dict.fromkeys(task.domain_tags)) or ("untagged",)
        phase = _phase_for_task(task)

        total.add(effective_status, reward_breakdown.total, failure_category)
        by_phase.setdefault(phase, _SummaryBucket()).add(
            effective_status,
            reward_breakdown.total,
            failure_category,
        )
        by_split.setdefault(split, _SummaryBucket()).add(
            effective_status,
            reward_breakdown.total,
            failure_category,
        )
        by_task_type.setdefault(task_type, _SummaryBucket()).add(
            effective_status,
            reward_breakdown.total,
            failure_category,
        )
        for domain in domains:
            by_domain.setdefault(domain, _SummaryBucket()).add(
                effective_status,
                reward_breakdown.total,
                failure_category,
            )

    return {
        "total": total.to_row(),
        "by_phase": _rows("phase", by_phase),
        "by_split": _rows("split", by_split),
        "by_domain": _rows("domain", by_domain),
        "by_task_type": _rows("task_type", by_task_type),
    }


def compare_baseline_on_split(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    baseline: str,
    split: str,
    allowed_placeholders_by_task: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, object]:
    """Build a held-out baseline report from paired attempts and verifier reports."""

    split_tasks = tuple(task for task in tasks if _enum_value(task.split) == split)
    if not split_tasks:
        raise ValueError(f"no benchmark tasks found for split `{split}`")

    return _compare_baseline_on_tasks(
        tasks,
        attempts,
        reports,
        baseline=baseline,
        selected_tasks=split_tasks,
        comparison_id=f"{baseline}::{split}",
        split_label=split,
        allowed_placeholders_by_task=allowed_placeholders_by_task,
    )


def _compare_baseline_on_tasks(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    baseline: str,
    selected_tasks: tuple[BenchmarkTask, ...],
    comparison_id: str,
    split_label: str,
    allowed_placeholders_by_task: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, object]:
    """Build a baseline report over an explicit benchmark task slice."""

    if len(attempts) != len(reports):
        raise ValueError("attempts and reports must have the same length")

    task_by_id = _task_index(tasks)
    if not selected_tasks:
        raise ValueError(f"no benchmark tasks found for slice `{split_label}`")

    pairs_by_task: dict[str, tuple[ProofAttempt, VerificationReport]] = {}
    for attempt, report in zip(attempts, reports, strict=True):
        if attempt.agent_key != baseline:
            continue
        if attempt.task_id in pairs_by_task:
            raise ValueError(f"duplicate attempt for baseline `{baseline}` and task `{attempt.task_id}`")
        pairs_by_task[attempt.task_id] = (attempt, report)

    allowed_by_task = _allowed_placeholders_by_task(tasks)
    if allowed_placeholders_by_task is not None:
        allowed_by_task.update({
            task_id: tuple(tokens)
            for task_id, tokens in allowed_placeholders_by_task.items()
        })

    rows: list[dict[str, object]] = []
    status_counts = _empty_status_counts()
    reward_total = 0.0
    premise_recall_total = 0.0
    failure_categories: dict[str, int] = {}

    for task in selected_tasks:
        pair = pairs_by_task.get(task.task_id)
        if pair is None:
            raise ValueError(f"missing attempt for baseline `{baseline}` and task `{task.task_id}`")
        attempt, report = pair
        if report.task_id != attempt.task_id:
            raise ValueError(
                f"attempt `{attempt.task_id}` paired with report for `{report.task_id}`"
            )
        if task_by_id.get(attempt.task_id) is None:
            raise ValueError(f"unknown benchmark task id: {attempt.task_id}")

        allowed_placeholders = tuple(allowed_by_task.get(task.task_id, ()))
        effective_status, reward_breakdown, first_error, violations = _evaluate_attempt_record(
            attempt,
            report,
            allowed_placeholders=allowed_placeholders,
        )
        failure_category = _failure_category(
            effective_status,
            first_error=first_error,
            diagnostics=report.diagnostics,
            violations=violations,
        )
        if failure_category:
            failure_categories[failure_category] = failure_categories.get(failure_category, 0) + 1

        expected_premises = tuple(task.expected_premises)
        premises_used = tuple(attempt.premises_used)
        premise_recall = _premise_recall(expected_premises, premises_used)
        premise_recall_total += premise_recall
        status_counts[effective_status.value] += 1
        reward_total += reward_breakdown.total

        rows.append(
            {
                "task_id": task.task_id,
                "task_type": _enum_value(task.task_type),
                "split": _enum_value(task.split),
                "difficulty": task.difficulty,
                "domain_tags": list(task.domain_tags),
                "agent_key": attempt.agent_key,
                "reported_status": _enum_value(report.status),
                "effective_status": effective_status.value,
                "passed": effective_status is VerificationStatus.ACCEPTED,
                "reward": reward_breakdown.total,
                "reward_components": dict(sorted(reward_breakdown.components.items())),
                "first_error": first_error,
                "failure_category": failure_category,
                "expected_premises": list(expected_premises),
                "premises_used": list(premises_used),
                "premise_recall": premise_recall,
                "allowed_placeholders": list(allowed_placeholders),
            }
        )

    total = len(rows)
    passed = status_counts[VerificationStatus.ACCEPTED.value]
    return {
        "comparison_id": comparison_id,
        "baseline": baseline,
        "split": split_label,
        "benchmark_task_count": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": passed / total if total else 0.0,
        "mean_reward": reward_total / total if total else 0.0,
        "mean_premise_recall": premise_recall_total / total if total else 0.0,
        "status_counts": status_counts,
        "failure_categories": dict(sorted(failure_categories.items())),
        "task_ids": [row["task_id"] for row in rows],
        "rows": rows,
    }


def build_paper_quality_heldout_report(
    tasks: tuple[BenchmarkTask, ...],
    attempts: tuple[ProofAttempt, ...],
    reports: tuple[VerificationReport, ...],
    *,
    baseline: str,
    split: str,
    proof_chains: tuple[Mapping[str, object], ...] = DEFAULT_PAPER_QUALITY_PROOF_CHAINS,
) -> dict[str, object]:
    """Build a paper-facing held-out report with theorem-chain coverage."""

    baseline_report = compare_baseline_on_split(
        tasks,
        attempts,
        reports,
        baseline=baseline,
        split=split,
    )
    chain_reports = [
        _proof_chain_report(chain, tasks, reports)
        for chain in proof_chains
    ]
    chain_count = len(chain_reports)
    chain_passed = sum(1 for report in chain_reports if report["status"] == "passed")
    heldout_domains = tuple(
        sorted({tag for row in baseline_report["rows"] for tag in row["domain_tags"]})
    )

    return {
        "report_id": f"paper-quality::{baseline}::{split}",
        "baseline": baseline,
        "split": split,
        "heldout_task_count": baseline_report["benchmark_task_count"],
        "heldout_pass_rate": baseline_report["pass_rate"],
        "heldout_domains": list(heldout_domains),
        "failure_taxonomy": {
            "failed": baseline_report["failed"],
            "status_counts": baseline_report["status_counts"],
            "failure_categories": baseline_report["failure_categories"],
        },
        "baseline_comparison": baseline_report,
        "non_seed_proof_chains": chain_reports,
        "non_seed_chain_count": chain_count,
        "non_seed_chain_passed": chain_passed,
        "non_seed_chain_pass_rate": chain_passed / chain_count if chain_count else 0.0,
        "notes": (
            "P8.M1 report: held-out baseline rows remain split-based, while "
            "non-seed proof chains audit reusable StatInference theorem routes "
            "that are not themselves benchmark items."
        ),
    }


def build_concrete_estimator_chain_report(
    tasks: tuple[BenchmarkTask, ...],
    reports: tuple[VerificationReport, ...],
    *,
    task_id: str = "paper_quality_ipw_hajek_concrete_chain_seed",
) -> dict[str, object]:
    """Build an auditable report for the concrete estimator proof chain."""

    task_by_id = _task_index(tasks)
    report_by_task = {report.task_id: report for report in reports}
    if task_id not in task_by_id:
        raise ValueError(f"unknown concrete estimator chain task id: {task_id}")

    task = task_by_id[task_id]
    report = report_by_task.get(task_id, VerificationReport(task_id, VerificationStatus.ERROR))
    component_task_ids = (
        "ipw_identification_certificate_seed",
        "ipw_hajek_scaled_linearization_route_seed",
        "constant_ipw_hajek_route_seed",
        "constant_ipw_hajek_exact_target_seed",
    )
    component_reports = [
        _component_report(component_id, task_by_id, report_by_task)
        for component_id in component_task_ids
    ]
    passed_components = sum(1 for component in component_reports if component["status"] == "passed")
    no_placeholder_policy = not task.lean_task.allowed_sorry
    passed = (
        report.status is VerificationStatus.ACCEPTED
        and no_placeholder_policy
        and passed_components == len(component_reports)
    )

    return {
        "report_id": "concrete-estimator-chain::ipw_hajek",
        "chain_id": "ipw_hajek_concrete_estimator_chain",
        "theorem": "StatInference.paperQualityIPWHajekConcreteEstimatorChain",
        "module": "StatInference.Examples.ConcreteEstimatorChain",
        "source_file": "StatInference/Examples/ConcreteEstimatorChain.lean",
        "benchmark_task_id": task_id,
        "verification_status": _enum_value(report.status),
        "passed": passed,
        "no_placeholder_policy": no_placeholder_policy,
        "expected_premises": list(task.expected_premises),
        "proof_components": component_reports,
        "component_count": len(component_reports),
        "component_passed": passed_components,
        "route_declarations": [
            "StatInference.paperQualityIPWHajekRate",
            "StatInference.paperQualityIPWHajekRoute",
            "StatInference.paperQualityIPWHajekConcreteEstimatorChain",
        ],
        "claims_verified": [
            "IPW identification conclusion is available on the concrete route.",
            "The constant Hajek estimator equals the target for every sample size.",
            "The centered numerator residual is zero for every sample size.",
            "The scaled linearization identity holds for every sample size.",
        ],
        "notes": (
            "P8.M2 concrete estimator chain: a single no-sorry Lean theorem "
            "composes the IPW/Hajek route through identification, exact target "
            "recovery, residual control, and scaled linearization."
        ),
    }


def build_ablation_report(
    tasks: tuple[BenchmarkTask, ...],
    paper_heldout: Mapping[str, object],
    concrete_chain: Mapping[str, object],
    training_manifest: Mapping[str, object],
    grpo_tasks: tuple[Mapping[str, object], ...],
    dpo_reports: tuple[Mapping[str, object], ...],
    lemma_proposal_gates: tuple[Mapping[str, object], ...],
    lemma_non_vacuity: tuple[Mapping[str, object], ...],
    lemma_proof_cost: tuple[Mapping[str, object], ...],
    lemma_ledger: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    """Build an artifact-backed ablation readiness report.

    This is intentionally a system-evidence ablation scaffold, not a trained
    model performance claim. It records whether each component needed for the
    P8 ablation is present, auditable, and backed by checked-in artifacts.
    """

    baseline_comparison = _mapping(paper_heldout.get("baseline_comparison"))
    mean_premise_recall = _float(baseline_comparison.get("mean_premise_recall"))
    heldout_pass_rate = _float(paper_heldout.get("heldout_pass_rate"))
    concrete_chain_passed = bool(concrete_chain.get("passed"))
    sft_examples = _sequence(training_manifest.get("sft_examples"))
    dpo_pairs = _sequence(training_manifest.get("dpo_pairs"))
    manifest_grpo_tasks = _sequence(training_manifest.get("grpo_tasks"))
    rejected_dpo_reports = sum(1 for report in dpo_reports if report.get("status") == "rejected")
    reward_components = sorted(
        {
            str(component)
            for task in grpo_tasks
            for component in _sequence(task.get("reward_components"))
        }
    )
    static_passed = sum(1 for report in lemma_proposal_gates if bool(report.get("passed")))
    non_vacuity_passed = sum(1 for report in lemma_non_vacuity if bool(report.get("passed")))
    proof_cost_passed = sum(1 for report in lemma_proof_cost if bool(report.get("passed")))
    blocked_placeholder_entries = sum(
        1 for entry in lemma_ledger if entry.get("status") == "blocked_placeholder"
    )
    curation_gate_count = (
        len(lemma_proposal_gates)
        + len(lemma_non_vacuity)
        + len(lemma_proof_cost)
    )
    curation_gate_passed = static_passed + non_vacuity_passed + proof_cost_passed

    components = [
        _ablation_component(
            "retrieval",
            mean_premise_recall,
            (
                f"held-out baseline mean premise recall is {mean_premise_recall:.3f} "
                "from expected-premise usage rows"
            ),
            "without retrieval evidence, expected local-stat lemma recall is not audited",
            mean_premise_recall > 0.0,
        ),
        _ablation_component(
            "sft",
            len(sft_examples),
            f"{len(sft_examples)} verified no-placeholder SFT examples are present in the manifest",
            "without SFT examples, the system has no domain-adaptation trace data",
            len(sft_examples) > 0,
        ),
        _ablation_component(
            "dpo",
            len(dpo_pairs),
            (
                f"{len(dpo_pairs)} chosen/rejected DPO pairs are present; "
                f"{rejected_dpo_reports} rejected attempts are Lean-labeled"
            ),
            "without DPO pairs, the prover lacks Lean-labeled contrast against invalid premises",
            len(dpo_pairs) > 0 and rejected_dpo_reports > 0,
        ),
        _ablation_component(
            "process_reward",
            len(grpo_tasks),
            (
                f"{len(grpo_tasks)} GRPO process-reward tasks expose "
                f"{len(reward_components)} reward components"
            ),
            "without process rewards, training falls back to sparse proof-complete feedback only",
            len(grpo_tasks) > 0 and "proof_complete" in reward_components,
        ),
        _ablation_component(
            "curation",
            curation_gate_passed,
            (
                f"{curation_gate_passed}/{curation_gate_count} proposal, non-vacuity, "
                f"and proof-cost gates pass; {blocked_placeholder_entries} placeholder-ledger "
                "entries remain blocked from library promotion"
            ),
            "without curation, generated lemmas could bypass duplicate, non-vacuity, or reuse checks",
            curation_gate_count > 0 and curation_gate_passed == curation_gate_count,
        ),
    ]
    full_system_ready = (
        heldout_pass_rate == 1.0
        and concrete_chain_passed
        and all(component["ready"] for component in components)
    )

    ablation_rows = [
        {
            "variant": "full_system",
            "status": "ready" if full_system_ready else "blocked",
            "expected_effect": (
                "all current P8 evidence is present and auditable"
                if full_system_ready
                else "one or more evidence components is missing"
            ),
            "removed_component": None,
            "primary_metric": heldout_pass_rate,
        }
    ]
    for component in components:
        ablation_rows.append(
            {
                "variant": f"no_{component['component']}",
                "status": "degraded",
                "expected_effect": component["disabled_effect"],
                "removed_component": component["component"],
                "primary_metric": 0.0,
            }
        )

    return {
        "report_id": "ablation::p8",
        "baseline": str(paper_heldout.get("baseline", "unknown")),
        "benchmark_task_count": len(tasks),
        "heldout_pass_rate": heldout_pass_rate,
        "concrete_chain_passed": concrete_chain_passed,
        "full_system_ready": full_system_ready,
        "components": components,
        "ablation_rows": ablation_rows,
        "evidence_summary": {
            "mean_premise_recall": mean_premise_recall,
            "sft_example_count": len(sft_examples),
            "dpo_pair_count": len(dpo_pairs),
            "dpo_rejected_report_count": rejected_dpo_reports,
            "grpo_process_task_count": len(grpo_tasks),
            "manifest_grpo_task_count": len(manifest_grpo_tasks),
            "process_reward_components": reward_components,
            "curation_gate_count": curation_gate_count,
            "curation_gate_passed": curation_gate_passed,
            "blocked_placeholder_ledger_entries": blocked_placeholder_entries,
        },
        "notes": (
            "P8.M3 report: artifact-backed ablation readiness for retrieval, SFT, "
            "DPO, Lean process reward, and curation. This is an auditable system "
            "component ablation scaffold, not a trained-model performance claim."
        ),
    }


def build_reproducibility_bundle(
    repo_root: Path,
    blueprint_report: Mapping[str, object],
    *,
    artifact_paths: tuple[str, ...] = DEFAULT_REPRODUCIBILITY_ARTIFACTS,
    validation_commands: tuple[Mapping[str, str], ...] = DEFAULT_REPRODUCIBILITY_COMMANDS,
    paper_draft_path: str = "docs/paper_draft.md",
) -> dict[str, object]:
    """Build a paper-facing reproducibility bundle with artifact hashes."""

    root = repo_root.resolve()
    artifact_records = [
        _artifact_record(root, artifact_path)
        for artifact_path in artifact_paths
    ]
    phase = _mapping(blueprint_report.get("current_phase"))
    milestone = _mapping(blueprint_report.get("current_milestone"))
    done_phase_count = int(blueprint_report.get("done_phase_count", 0))
    phase_count = int(blueprint_report.get("phase_count", 0))
    all_phases_done = phase_count > 0 and done_phase_count == phase_count

    return {
        "report_id": "reproducibility::p8",
        "blueprint_id": str(blueprint_report.get("blueprint_id", "")),
        "blueprint_title": str(blueprint_report.get("title", "")),
        "phase_count": phase_count,
        "done_phase_count": done_phase_count,
        "all_phases_done": all_phases_done,
        "current_phase": dict(phase),
        "current_milestone": dict(milestone) if milestone else None,
        "paper_draft_path": paper_draft_path,
        "artifact_count": len(artifact_records),
        "artifacts": artifact_records,
        "validation_commands": [dict(command) for command in validation_commands],
        "reproduction_order": [
            "Install Python development dependencies with pip install -e \".[dev]\".",
            "Run the validation_commands in order from this report.",
            "Compare artifact sha256 values against the artifacts table.",
            "Use docs/paper_draft.md as the paper narrative tied to these artifacts.",
            "Use config/statlean_blueprint.json as the executable progress contract.",
        ],
        "guardrails": [
            "No promoted StatInference theorem may rely on forbidden proof shortcuts.",
            "Training artifacts are preparation data, not evidence of a trained model improvement.",
            "Ablation rows are system-component readiness ablations, not a model-performance claim.",
            "Statistical semantics and new theorem statements still require human review.",
        ],
        "notes": (
            "P8.M4 reproducibility bundle: hash-pinned artifacts, executable "
            "validation commands, paper draft linkage, and explicit guardrails."
        ),
    }


def build_external_baseline_plan(
    tasks: tuple[BenchmarkTask, ...],
    *,
    split: str = "test",
    baseline_specs: tuple[Mapping[str, object], ...] = DEFAULT_EXTERNAL_BASELINES,
    benchmark_path: str = "benchmarks/seeds.jsonl",
    output_dir: str = "artifacts/external_baselines",
) -> dict[str, object]:
    """Build a concrete run plan for post-P8 external prover baselines."""

    split_tasks = tuple(task for task in tasks if _enum_value(task.split) == split)
    if not split_tasks:
        raise ValueError(f"no benchmark tasks found for split `{split}`")

    theorem_hole_tasks = tuple(task for task in tasks if task.lean_task.allowed_sorry)
    domain_tags = sorted({tag for task in split_tasks for tag in task.domain_tags})
    baselines = [
        _external_baseline_row(
            spec,
            split=split,
            benchmark_path=benchmark_path,
            output_dir=output_dir,
            task_count=len(split_tasks),
        )
        for spec in baseline_specs
    ]
    ready_count = sum(1 for baseline in baselines if baseline["status"] == "ready")

    return {
        "report_id": f"external-baseline-plan::{split}",
        "split": split,
        "benchmark_path": benchmark_path,
        "benchmark_task_count": len(tasks),
        "target_task_count": len(split_tasks),
        "target_task_ids": [task.task_id for task in split_tasks],
        "target_domain_tags": domain_tags,
        "theorem_hole_task_count": len(theorem_hole_tasks),
        "theorem_hole_task_ids": [task.task_id for task in theorem_hole_tasks],
        "baseline_count": len(baselines),
        "ready_baseline_count": ready_count,
        "blocked_baseline_count": len(baselines) - ready_count,
        "baselines": baselines,
        "metrics": [
            "pass_at_1",
            "pass_at_8",
            "pass_at_32",
            "valid_tactic_rate",
            "mean_premise_recall",
            "unknown_identifier_rate",
            "timeout_rate",
            "mean_wall_time_seconds",
        ],
        "promotion_gate": (
            "An external baseline row is reportable only after attempts are captured "
            "as ProofAttempt JSONL, verified by the local Lake verifier, and summarized "
            "with the same failure taxonomy as the seed-registry baseline."
        ),
        "notes": (
            "P9.M1 plan: external prover baselines are specified as reproducible run "
            "targets. Only seed-registry is currently ready; model baselines remain "
            "blocked until their adapters and credentials/checkpoints are available."
        ),
    }


def build_external_baseline_results(
    tasks: tuple[BenchmarkTask, ...],
    plan: Mapping[str, object],
    attempts_by_baseline: Mapping[str, tuple[ProofAttempt, ...]],
    reports_by_baseline: Mapping[str, tuple[VerificationReport, ...]],
    *,
    source_by_baseline: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Normalize available external baseline results against the planned split."""

    split = str(plan.get("split", "test"))
    baselines = tuple(_mapping(row) for row in plan.get("baselines", ()))
    source_by_baseline = source_by_baseline or {}
    rows = [
        _external_baseline_result_row(
            tasks,
            baseline,
            split=split,
            attempts=attempts_by_baseline.get(str(baseline.get("baseline_id", ""))),
            reports=reports_by_baseline.get(str(baseline.get("baseline_id", ""))),
            source=source_by_baseline.get(str(baseline.get("baseline_id", "")), "missing"),
        )
        for baseline in baselines
    ]
    ingested_rows = [row for row in rows if row["ingestion_status"] == "ingested"]
    blocked_rows = [row for row in rows if row["ingestion_status"] != "ingested"]
    best = max(
        ingested_rows,
        key=lambda row: (
            float(row["pass_rate"]),
            float(row["mean_premise_recall"]),
            str(row["baseline_id"]),
        ),
        default=None,
    )

    return {
        "report_id": f"external-baseline-results::{split}",
        "plan_report_id": str(plan.get("report_id", "")),
        "split": split,
        "baseline_count": len(rows),
        "ingested_count": len(ingested_rows),
        "blocked_count": len(blocked_rows),
        "best_available_baseline": best["baseline_id"] if best else None,
        "rows": rows,
        "comparison_policy": (
            "Each external baseline must provide ProofAttempt and VerificationReport "
            "JSONL records over the planned split. Results are compared with "
            "compare_baseline_on_split, so policy violations, premise recall, "
            "failure taxonomy, and effective pass rate match the seed-registry "
            "evaluation path."
        ),
        "notes": (
            "P9.M3 ingestion: seed-registry is ingested from checked-in verifier "
            "artifacts when planned external-baseline files are not present; model "
            "baselines remain blocked until adapters produce attempt/report JSONL."
        ),
    }


def build_empirical_process_external_prover_slice(
    tasks: tuple[BenchmarkTask, ...],
    target_report: Mapping[str, object],
    attempts_by_baseline: Mapping[str, tuple[ProofAttempt, ...]],
    reports_by_baseline: Mapping[str, tuple[VerificationReport, ...]],
    *,
    source_by_baseline: Mapping[str, str] | None = None,
    baseline_specs: tuple[Mapping[str, object], ...] = DEFAULT_EXTERNAL_BASELINES,
    benchmark_path: str = "benchmarks/seeds.jsonl",
    output_dir: str = "artifacts/external_baselines/empirical_process",
    interface_families: tuple[str, ...] = DEFAULT_EMPIRICAL_PROCESS_EXTERNAL_FAMILIES,
) -> dict[str, object]:
    """Build the P10 empirical-process external prover evaluation slice.

    Unlike the generic held-out baseline plan, this slice targets all checked-in
    benchmark tasks attached to the bracketing, VC-subgraph, and Donsker
    families.  External model adapters remain separately blocked until they
    provide ProofAttempt and VerificationReport JSONL files for this slice.
    """

    source_by_baseline = source_by_baseline or {}
    requested_families = set(interface_families)
    target_rows = [
        _mapping(row)
        for row in target_report.get("targets", ())
        if str(_mapping(row).get("interface_family", "")) in requested_families
    ]
    if not target_rows:
        raise ValueError("no empirical-process target rows found for requested families")

    task_by_id = _task_index(tasks)
    family_rows = [
        _empirical_process_external_family_row(
            row,
            task_by_id,
            attempts_by_baseline.get("seed-registry", ()),
            reports_by_baseline.get("seed-registry", ()),
        )
        for row in target_rows
    ]
    selected_task_ids = tuple(
        task.task_id
        for task in tasks
        if any(task.task_id in family["task_ids"] for family in family_rows)
    )
    selected_tasks = tuple(task for task in tasks if task.task_id in set(selected_task_ids))
    if not selected_tasks:
        raise ValueError("empirical-process external slice has no benchmark tasks")

    baselines = [
        _external_baseline_row(
            spec,
            split="empirical-process",
            benchmark_path=benchmark_path,
            output_dir=output_dir,
            task_count=len(selected_tasks),
        )
        for spec in baseline_specs
    ]
    rows = [
        _external_baseline_result_row(
            tasks,
            baseline,
            split="empirical-process",
            attempts=attempts_by_baseline.get(str(baseline.get("baseline_id", ""))),
            reports=reports_by_baseline.get(str(baseline.get("baseline_id", ""))),
            source=source_by_baseline.get(str(baseline.get("baseline_id", "")), "missing"),
            selected_tasks=selected_tasks,
            comparison_id=f"{baseline.get('baseline_id', '')}::empirical_process_external_slice",
        )
        for baseline in baselines
    ]
    ingested_rows = [row for row in rows if row["ingestion_status"] == "ingested"]
    blocked_rows = [row for row in rows if row["ingestion_status"] != "ingested"]
    best = max(
        ingested_rows,
        key=lambda row: (
            float(row["pass_rate"]),
            float(row["mean_premise_recall"]),
            str(row["baseline_id"]),
        ),
        default=None,
    )

    return {
        "report_id": "empirical-process-external-prover-slice::p10",
        "target_report_id": str(target_report.get("report_id", "")),
        "interface_families": list(interface_families),
        "family_count": len(family_rows),
        "families": family_rows,
        "benchmark_path": benchmark_path,
        "target_task_count": len(selected_tasks),
        "target_task_ids": list(selected_task_ids),
        "baseline_count": len(rows),
        "ingested_count": len(ingested_rows),
        "blocked_count": len(blocked_rows),
        "best_available_baseline": best["baseline_id"] if best else None,
        "rows": rows,
        "adapter_contract": (
            "Each external prover adapter must emit ProofAttempt JSONL and "
            "VerificationReport JSONL over exactly this empirical-process task "
            "slice before it is compared with seed-registry evidence."
        ),
        "acceptance_gates": [
            "The family slice must include bracketing, VC-subgraph, and Donsker benchmark tasks.",
            "Seed-registry evidence must be verified by the local Lake verifier for every task in the slice.",
            "External model rows remain blocked until adapter-produced attempts and verifier reports are checked in.",
            "Blocked external rows must preserve concrete missing-runtime or missing-result-file reasons.",
        ],
        "notes": (
            "P10.M5 materializes the empirical-process external prover slice "
            "separately from the generic held-out split, so bracketing, "
            "VC-subgraph, and Donsker benchmark families can be evaluated "
            "together once external prover adapters are available."
        ),
    }


def build_vdvw_theorem_inventory(
    tasks: tuple[BenchmarkTask, ...],
    *,
    inventory_specs: tuple[Mapping[str, object], ...] = DEFAULT_VDVW_THEOREM_INVENTORY,
    markdown_root: str = VDVW_MARKDOWN_ROOT,
) -> dict[str, object]:
    """Build a source-linked VdV&W theorem inventory for P11.

    The report is an audit artifact, not a theorem-completion claim.  It maps
    textbook anchors to current Lean declarations, benchmark evidence, missing
    primitives, and semantic risks before any new statement is promoted.
    """

    task_by_id = _task_index(tasks)
    rows = [
        _vdvw_inventory_row(spec, task_by_id, markdown_root=markdown_root)
        for spec in inventory_specs
    ]
    family_counts: dict[str, int] = {}
    tier_counts: dict[str, int] = {}
    claim_level_counts: dict[str, int] = {}
    for row in rows:
        family = str(row["interface_family"])
        tier = str(row["formalization_tier"])
        claim_level = str(row["current_claim_level"])
        family_counts[family] = family_counts.get(family, 0) + 1
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        claim_level_counts[claim_level] = claim_level_counts.get(claim_level, 0) + 1

    blocked_rows = [
        row for row in rows
        if row["promotion_status"] != "ready_for_statement_candidate"
    ]

    return {
        "report_id": "vdvw-theorem-inventory::p11.m1",
        "source": "van der Vaart and Wellner, Weak Convergence and Empirical Processes",
        "markdown_root": markdown_root,
        "row_count": len(rows),
        "family_counts": dict(sorted(family_counts.items())),
        "formalization_tier_counts": dict(sorted(tier_counts.items())),
        "claim_level_counts": dict(sorted(claim_level_counts.items())),
        "blocked_or_review_rows": [str(row["inventory_id"]) for row in blocked_rows],
        "rows": rows,
        "acceptance_gates": [
            "Do not promote a source theorem unless every assumption has a Lean definition or an explicit proof-carrying field.",
            "Do not mark bridge or certificate interfaces as the exact VdV&W theorem.",
            "Record outer-probability, measurability, separability, envelope, tightness, and entropy-integral gaps explicitly.",
            "Use AXLE only for auxiliary extraction/checking; local Lake remains the acceptance authority.",
            "Keep textbook assets local-only and cite short anchors rather than long copied excerpts.",
        ],
        "notes": (
            "P11.M1 inventory: source-linked theorem cards for bracketing, "
            "VC-subgraph, and Donsker targets.  Rows are designed to prevent "
            "semantic drift before autoformalization or Lean theorem promotion."
        ),
    }


def build_vdvw_bracketing_gc_statement_candidates(
    tasks: tuple[BenchmarkTask, ...],
    *,
    candidate_specs: tuple[Mapping[str, object], ...] = DEFAULT_VDVW_BRACKETING_GC_STATEMENT_CANDIDATES,
    source_anchors: tuple[Mapping[str, object], ...] = DEFAULT_VDVW_BRACKETING_GC_SOURCE_ANCHORS,
    markdown_root: str = VDVW_MARKDOWN_ROOT,
) -> dict[str, object]:
    """Build P11.M2 statement candidates for the VdV&W 2.4.1 route.

    This artifact is intentionally below theorem-report level: it records
    source-linked statement options, proof obligations, and validation hooks
    before any candidate is promoted to a claimed Lean theorem.
    """

    task_by_id = _task_index(tasks)
    candidates = [
        _vdvw_statement_candidate_row(spec, task_by_id)
        for spec in candidate_specs
    ]
    status_counts: dict[str, int] = {}
    track_counts: dict[str, int] = {}
    for candidate in candidates:
        status = str(candidate["status"])
        track = str(candidate["track"])
        status_counts[status] = status_counts.get(status, 0) + 1
        track_counts[track] = track_counts.get(track, 0) + 1

    blocked_or_review = [
        str(candidate["candidate_id"])
        for candidate in candidates
        if candidate["human_review_required"]
        or not str(candidate["status"]).startswith("compiled")
    ]

    return {
        "report_id": "vdvw-bracketing-gc-statement-candidates::p11.m2",
        "source_inventory_id": "vdvw-2.4.1-finite-bracketing-gc",
        "source_label": "Theorem 2.4.1",
        "source": "van der Vaart and Wellner, Weak Convergence and Empirical Processes",
        "markdown_root": markdown_root,
        "source_anchors": [
            {
                "anchor_id": str(anchor["anchor_id"]),
                "label": str(anchor["label"]),
                "markdown_anchor": {
                    "root": markdown_root,
                    "segment": str(anchor["segment"]),
                    "line_start": int(anchor["line_start"]),
                    "line_end": int(anchor["line_end"]),
                },
                "purpose": str(anchor["purpose"]),
            }
            for anchor in source_anchors
        ],
        "candidate_count": len(candidates),
        "status_counts": dict(sorted(status_counts.items())),
        "track_counts": dict(sorted(track_counts.items())),
        "blocked_or_review_candidates": blocked_or_review,
        "candidates": candidates,
        "acceptance_gates": [
            "This artifact is a statement-candidate plan, not a formal theorem report.",
            "The dependency-minimal route may reuse compiled bridge declarations but must not be labeled as exact VdV&W Theorem 2.4.1.",
            "The primitive L1 bracketing-number candidate needs explicit endpoint, finite-norm, and non-vacuity assumptions before Lean promotion.",
            "The exact textbook target remains blocked until outer-probability and empirical-measure semantics exist.",
            "Any AXLE-generated output must be rechecked by local Lake and must not weaken the source theorem statement.",
        ],
        "next_actions": [
            "Add theorem-hole benchmark seeds for the primitive L1 bracketing-number constructor.",
            "Draft Lean signatures for L1BracketingNumber and FiniteL1BracketingNumberAtEveryScale without claiming proof.",
            "Keep exact outer-almost-sure theorem as a theorem card until the outer-probability layer is available.",
        ],
        "notes": (
            "P11.M2 converts the VdV&W Theorem 2.4.1 inventory row into "
            "three statement-candidate tracks: compiled bridge, next primitive "
            "constructor, and exact outer-almost-sure textbook target."
        ),
    }


def build_vdvw_vc_donsker_proof_obligations(
    tasks: tuple[BenchmarkTask, ...],
    *,
    obligation_specs: tuple[Mapping[str, object], ...] = DEFAULT_VDVW_VC_DONSKER_PROOF_OBLIGATIONS,
    source_anchors: tuple[Mapping[str, object], ...] = DEFAULT_VDVW_VC_DONSKER_SOURCE_ANCHORS,
    markdown_root: str = VDVW_MARKDOWN_ROOT,
) -> dict[str, object]:
    """Build P11.M3 proof-obligation cards for VdV&W VC/Donsker targets."""

    task_by_id = _task_index(tasks)
    obligations = [
        _vdvw_proof_obligation_row(spec, task_by_id)
        for spec in obligation_specs
    ]
    status_counts: dict[str, int] = {}
    track_counts: dict[str, int] = {}
    for obligation in obligations:
        status = str(obligation["status"])
        track = str(obligation["track"])
        status_counts[status] = status_counts.get(status, 0) + 1
        track_counts[track] = track_counts.get(track, 0) + 1

    return {
        "report_id": "vdvw-vc-donsker-proof-obligations::p11.m3",
        "source_inventory_ids": [
            "vdvw-2.5.2-uniform-entropy-donsker",
            "vdvw-2.5.6-bracketing-donsker",
            "vdvw-2.6.4-vc-set-entropy",
            "vdvw-2.6.7-vc-subgraph-entropy",
            "vdvw-2.6.8-vc-subgraph-donsker",
        ],
        "source": "van der Vaart and Wellner, Weak Convergence and Empirical Processes",
        "markdown_root": markdown_root,
        "source_anchors": [
            {
                "anchor_id": str(anchor["anchor_id"]),
                "label": str(anchor["label"]),
                "markdown_anchor": {
                    "root": markdown_root,
                    "segment": str(anchor["segment"]),
                    "line_start": int(anchor["line_start"]),
                    "line_end": int(anchor["line_end"]),
                },
                "purpose": str(anchor["purpose"]),
            }
            for anchor in source_anchors
        ],
        "obligation_count": len(obligations),
        "status_counts": dict(sorted(status_counts.items())),
        "track_counts": dict(sorted(track_counts.items())),
        "blocked_obligations": [
            str(obligation["obligation_id"])
            for obligation in obligations
            if str(obligation["status"]).startswith("blocked")
        ],
        "obligations": obligations,
        "acceptance_gates": [
            "This artifact records proof obligations only; it is not a theorem-completion report.",
            "VC set-class entropy, VC-subgraph entropy, and Donsker weak convergence must stay separate.",
            "A GC certificate must not be promoted into Donsker evidence.",
            "Pre-Gaussianity, tightness, weak envelope tails, separability, and outer measurability must be explicit before exact theorem promotion.",
            "AXLE may assist extraction/checking, but local Lake and no-shortcut scans remain the acceptance authority.",
        ],
        "next_actions": [
            "Start P12.M1 by designing primitive empirical sample and outer-convergence semantics.",
            "Add theorem-hole benchmarks for VC set entropy, VC-subgraph entropy, and Donsker weak-convergence constructors.",
            "Keep downstream estimator normality handoffs behind DonskerAsymptoticNormalityRoute until a real Donsker constructor is available.",
        ],
        "notes": (
            "P11.M3 source-links VdV&W VC and Donsker targets to the "
            "missing Lean primitives and proof obligations needed before "
            "any exact theorem claim."
        ),
    }


def build_vdvw_primitive_empirical_semantics(
    tasks: tuple[BenchmarkTask, ...],
    *,
    primitive_specs: tuple[Mapping[str, object], ...] = DEFAULT_VDVW_PRIMITIVE_EMPIRICAL_SEMANTICS,
    source_anchors: tuple[Mapping[str, object], ...] = DEFAULT_VDVW_PRIMITIVE_SEMANTICS_SOURCE_ANCHORS,
    markdown_root: str = VDVW_MARKDOWN_ROOT,
) -> dict[str, object]:
    """Build P12.M1 primitive empirical-process semantics design artifact."""

    task_by_id = _task_index(tasks)
    primitives = [
        _vdvw_primitive_semantics_row(spec, task_by_id)
        for spec in primitive_specs
    ]
    status_counts: dict[str, int] = {}
    layer_counts: dict[str, int] = {}
    planned_seed_ids: list[str] = []
    for primitive in primitives:
        status = str(primitive["status"])
        layer = str(primitive["layer"])
        status_counts[status] = status_counts.get(status, 0) + 1
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
        planned_seed_ids.extend(str(seed_id) for seed_id in primitive["planned_theorem_hole_seed_ids"])

    blocked = [
        str(primitive["primitive_id"])
        for primitive in primitives
        if str(primitive["status"]).startswith("blocked")
    ]
    design_ready = [
        str(primitive["primitive_id"])
        for primitive in primitives
        if "ready" in str(primitive["status"])
    ]

    return {
        "report_id": "vdvw-primitive-empirical-semantics::p12.m1",
        "source": "van der Vaart and Wellner, Weak Convergence and Empirical Processes",
        "markdown_root": markdown_root,
        "depends_on_artifacts": [
            "artifacts/research/vdvw-theorem-inventory.json",
            "artifacts/research/vdvw-bracketing-gc-statement-candidates.json",
            "artifacts/research/vdvw-vc-donsker-proof-obligations.json",
        ],
        "source_anchors": [
            {
                "anchor_id": str(anchor["anchor_id"]),
                "label": str(anchor["label"]),
                "markdown_anchor": {
                    "root": markdown_root,
                    "segment": str(anchor["segment"]),
                    "line_start": int(anchor["line_start"]),
                    "line_end": int(anchor["line_end"]),
                },
                "purpose": str(anchor["purpose"]),
            }
            for anchor in source_anchors
        ],
        "primitive_count": len(primitives),
        "status_counts": dict(sorted(status_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "design_ready_primitives": design_ready,
        "blocked_primitives": blocked,
        "planned_theorem_hole_seed_count": len(tuple(dict.fromkeys(planned_seed_ids))),
        "planned_theorem_hole_seed_ids": list(dict.fromkeys(planned_seed_ids)),
        "primitives": primitives,
        "acceptance_gates": [
            "This artifact is a semantics design artifact, not a theorem-completion report.",
            "Every promoted Lean primitive must compile under local Lake and keep the no-sorry/no-admit/no-axiom/no-unsafe policy.",
            "Empirical sample semantics, outer convergence, bracketing numbers, and Donsker weak convergence must stay separate.",
            "Exact VdV&W theorem claims require source anchors, non-vacuity examples, and successful benchmark/theorem-hole promotion.",
            "AXLE may check or repair candidate code, but local Lake validation remains the public acceptance authority.",
        ],
        "next_actions": [
            "Continue P12.M3 by tying measure-backed endpoint semantics to concrete iid empirical measures and endpoint SLLN events.",
            "Materialize the remaining theorem-hole benchmark seed for the exact outer almost-sure statement only after outer convergence constructors compile.",
            "Keep the exact outer-almost-sure Theorem 2.4.1 blocked until outer convergence constructors and non-vacuity examples are promoted.",
        ],
        "notes": (
            "P12.M1/P12.M2/P12.M3 map the source-linked VdV&W theorem-card gaps into "
            "concrete Lean API signature targets, proof-carrying L1 bracketing "
            "number witnesses, finite endpoint assembly, sample-average endpoint "
            "semantics, measure-backed endpoint integrals, outer-convergence "
            "signatures, and theorem-hole seed names. "
            "It deliberately separates current compiled handoffs from future "
            "primitive semantics so autoformalization cannot silently weaken "
            "outer convergence, bracketing-number, or Donsker assumptions."
        ),
    }


def build_empirical_process_expansion_targets(
    tasks: tuple[BenchmarkTask, ...],
    *,
    target_specs: tuple[Mapping[str, object], ...] = DEFAULT_EMPIRICAL_PROCESS_EXPANSION_TARGETS,
) -> dict[str, object]:
    """Build the P9 empirical-process expansion target map.

    The artifact records scoped Lean interfaces and next theorem targets.  It is
    deliberately not a performance claim: bracketing, VC, and Donsker rows are
    accepted only as proof-carrying interface targets until downstream theorems
    and non-vacuity examples are added.
    """

    task_ids_by_tag = _task_ids_by_tag(tasks)
    rows = [
        _empirical_process_target_row(spec, task_ids_by_tag)
        for spec in target_specs
    ]
    scoped_rows = [
        row for row in rows
        if row["status"] in {"interface_scoped", "implemented_seed_interface"}
    ]
    pending_rows = [row for row in rows if row["status"] == "pending"]

    return {
        "report_id": "empirical-process-targets::p9",
        "target_count": len(rows),
        "scoped_count": len(scoped_rows),
        "pending_count": len(pending_rows),
        "benchmark_task_ids_by_tag": {
            tag: task_ids_by_tag[tag]
            for tag in sorted(task_ids_by_tag)
            if tag in {
                "bracketing_number",
                "covering_number",
                "donsker",
                "empirical_process",
                "glivenko_cantelli",
                "rademacher_complexity",
                "vc_subgraph",
            }
        },
        "targets": rows,
        "acceptance_gates": [
            "Lean module compiles with no sorry/admit/unsafe/axiom in promoted StatInference sources.",
            "Every interface remains proof-carrying: no entropy, VC, or Donsker theorem is asserted without a supplied proof field.",
            "At least one benchmark seed or theorem-hole target cites each active interface family before claiming model-evaluation coverage.",
            "Each promoted empirical-process theorem must include a non-vacuity example or concrete satisfying certificate.",
            "Human statistical review is required before replacing abstract interface fields with primitive theorem statements.",
        ],
        "notes": (
            "P9.M4 scopes the next empirical-process layer around bracketing, "
            "VC-subgraph, and Donsker proof-carrying interfaces, while retaining "
            "the already implemented covering-number and Rademacher seed routes."
        ),
    }


@dataclass
class _SummaryBucket:
    attempts: int = 0
    passed: int = 0
    reward_total: float = 0.0
    failure_categories: dict[str, int] = field(default_factory=dict)

    def add(
        self,
        status: VerificationStatus,
        reward: float,
        failure_category: str | None,
    ) -> None:
        self.attempts += 1
        self.reward_total += reward
        if status is VerificationStatus.ACCEPTED:
            self.passed += 1
            return
        if failure_category:
            self.failure_categories[failure_category] = (
                self.failure_categories.get(failure_category, 0) + 1
            )

    def to_row(self) -> dict[str, object]:
        return {
            "attempts": self.attempts,
            "passed": self.passed,
            "failed": self.attempts - self.passed,
            "mean_reward": self.reward_total / self.attempts if self.attempts else 0.0,
            "failure_categories": dict(sorted(self.failure_categories.items())),
        }


def _evaluate_attempt_record(
    attempt: ProofAttempt,
    report: VerificationReport,
    *,
    allowed_placeholders: Iterable[str] = (),
    diagnostics: list[str] | None = None,
) -> tuple[
    VerificationStatus,
    RewardBreakdown,
    str | None,
    tuple[object, ...],
]:
    status = _normalize_status(report.status, report.task_id, diagnostics if diagnostics is not None else [])
    observations = scan_policy_tokens(
        attempt.lean_code,
        allowed_placeholders=allowed_placeholders,
    )
    violations = tuple(occurrence for occurrence in observations if not occurrence.allowed)
    if diagnostics is not None:
        diagnostics.extend(f"{attempt.task_id}: {occurrence.diagnostic}" for occurrence in observations)

    effective_status = status
    first_error = report.first_error
    if violations and status is VerificationStatus.ACCEPTED:
        first = violations[0]
        effective_status = VerificationStatus.REJECTED
        first_error = f"forbidden token `{first.token}` at line {first.line}, column {first.column}"
        if diagnostics is not None:
            diagnostics.append(
                f"{attempt.task_id}: accepted report overridden to rejected because policy violations were found"
            )

    scoring_report = VerificationReport(
        task_id=report.task_id,
        status=effective_status,
        locally_valid_steps=report.locally_valid_steps,
        closed_goals=report.closed_goals,
        first_error=first_error,
        diagnostics=report.diagnostics,
    )
    return (
        effective_status,
        score_attempt(
            attempt,
            scoring_report,
            allowed_placeholders=allowed_placeholders,
        ),
        first_error,
        violations,
    )


def _failure_category(
    status: VerificationStatus,
    *,
    first_error: str | None,
    diagnostics: Iterable[str],
    violations: Iterable[object],
) -> str | None:
    if status is VerificationStatus.ACCEPTED:
        return None
    if status is VerificationStatus.TIMEOUT:
        return "timeout"

    text = " ".join(part for part in (first_error, *diagnostics) if part).lower()
    if "lake executable not found" in text:
        return "missing_lake"
    if "unknown module" in text or "module not found" in text or "invalid import" in text:
        return "import_error"
    if "forbidden token" in text or tuple(violations):
        return "policy_violation"
    if "unknown declaration" in text or "unknown constant" in text or "unknown identifier" in text:
        return "unknown_declaration"
    if "type mismatch" in text or "application type mismatch" in text or "failed to synthesize" in text:
        return "type_mismatch"
    if "unsolved goal" in text:
        return "unsolved_goals"
    if status is VerificationStatus.ERROR:
        return "verifier_error"
    return "rejected"


def _task_index(tasks: tuple[BenchmarkTask, ...]) -> dict[str, BenchmarkTask]:
    task_by_id: dict[str, BenchmarkTask] = {}
    for task in tasks:
        if task.task_id in task_by_id:
            raise ValueError(f"duplicate benchmark task id: {task.task_id}")
        task_by_id[task.task_id] = task
    return task_by_id


def _phase_for_task(task: BenchmarkTask) -> str:
    tags = set(task.domain_tags)
    if tags & {"theorem_hole", "multi_goal"}:
        return "P5"
    if tags & {
        "aipw",
        "ate",
        "causal_bridge",
        "causal_identification",
        "double_robust",
        "hajek_ipw",
        "influence_function",
        "ipw",
        "neyman_orthogonality",
        "orthogonal_score",
        "potential_outcomes",
        "product_rate",
        "second_order_remainder",
        "semiparametric",
    }:
        return "P4"
    if tags & {
        "argmin_consistency",
        "asymptotic_bridge",
        "asymptotic_linearity",
        "asymptotic_normality",
        "asymptotic_scaling",
        "bridge",
        "clt",
        "delta_method",
        "estimator_transformation",
        "m_estimation",
        "slutsky",
        "z_estimation",
    }:
        return "P3"
    if tags & {
        "bracketing_number",
        "covering_number",
        "donsker",
        "empirical_average",
        "empirical_process",
        "empirical_risk",
        "finite_class_gc",
        "finite_union",
        "glivenko_cantelli",
        "notation",
        "projection",
        "rademacher_complexity",
        "uniform_deviation",
        "vc_subgraph",
    }:
        return "P2"
    if tags & {
        "asymptotic_calculus",
        "convergence",
        "erm_consistency",
        "estimator_algebra",
        "estimator_interface",
        "probability_convergence",
        "ratio_estimator",
        "weak_convergence",
    }:
        return "P1"
    return "unmapped"


def _allowed_placeholders_by_task(tasks: tuple[BenchmarkTask, ...]) -> dict[str, tuple[str, ...]]:
    return {task.task_id: ("sorry",) if task.lean_task.allowed_sorry else () for task in tasks}


def _rows(label: str, buckets: Mapping[str, _SummaryBucket]) -> list[dict[str, object]]:
    rows = []
    for key in sorted(buckets):
        rows.append({label: key, **buckets[key].to_row()})
    return rows


def _proof_chain_report(
    chain: Mapping[str, object],
    tasks: tuple[BenchmarkTask, ...],
    reports: tuple[VerificationReport, ...],
) -> dict[str, object]:
    task_ids = tuple(str(task_id) for task_id in chain.get("benchmark_task_ids", ()))
    report_by_task = {report.task_id: report for report in reports}
    known_task_ids = {task.task_id for task in tasks}
    accepted_task_ids = tuple(
        task_id
        for task_id in task_ids
        if task_id in known_task_ids
        and report_by_task.get(task_id, VerificationReport(task_id, VerificationStatus.ERROR)).status
        is VerificationStatus.ACCEPTED
    )
    missing_task_ids = tuple(task_id for task_id in task_ids if task_id not in accepted_task_ids)
    pass_rate = len(accepted_task_ids) / len(task_ids) if task_ids else 0.0
    status = "passed" if task_ids and not missing_task_ids else "blocked"
    return {
        "chain_id": str(chain["chain_id"]),
        "name": str(chain["name"]),
        "source_module": str(chain["source_module"]),
        "benchmark_task_ids": list(task_ids),
        "required_declarations": list(chain.get("required_declarations", ())),
        "accepted_task_ids": list(accepted_task_ids),
        "missing_task_ids": list(missing_task_ids),
        "pass_rate": pass_rate,
        "status": status,
    }


def _component_report(
    task_id: str,
    task_by_id: Mapping[str, BenchmarkTask],
    report_by_task: Mapping[str, VerificationReport],
) -> dict[str, object]:
    task = task_by_id.get(task_id)
    report = report_by_task.get(task_id, VerificationReport(task_id, VerificationStatus.ERROR))
    status = "passed" if task is not None and report.status is VerificationStatus.ACCEPTED else "blocked"
    return {
        "task_id": task_id,
        "status": status,
        "verification_status": _enum_value(report.status),
        "expected_premises": list(task.expected_premises) if task is not None else [],
    }


def _ablation_component(
    component: str,
    enabled_metric: float | int,
    enabled_evidence: str,
    disabled_effect: str,
    ready: bool,
) -> dict[str, object]:
    return {
        "component": component,
        "ready": ready,
        "enabled_metric": enabled_metric,
        "enabled_evidence": enabled_evidence,
        "disabled_effect": disabled_effect,
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _artifact_record(repo_root: Path, relative_path: str) -> dict[str, object]:
    path = repo_root / relative_path
    if not path.exists():
        raise ValueError(f"missing reproducibility artifact: {relative_path}")
    payload = path.read_bytes()
    text = payload.decode("utf-8")
    return {
        "path": relative_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_count": len(payload),
        "line_count": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
    }


def _task_ids_by_tag(tasks: tuple[BenchmarkTask, ...]) -> dict[str, list[str]]:
    task_ids_by_tag: dict[str, list[str]] = {}
    for task in tasks:
        for tag in task.domain_tags:
            task_ids_by_tag.setdefault(tag, []).append(task.task_id)
    return {tag: sorted(task_ids) for tag, task_ids in task_ids_by_tag.items()}


def _empirical_process_target_row(
    spec: Mapping[str, object],
    task_ids_by_tag: Mapping[str, list[str]],
) -> dict[str, object]:
    benchmark_tags = tuple(str(tag) for tag in _sequence(spec.get("benchmark_tags")))
    interface_family = str(spec["interface_family"])
    family_tags = _empirical_process_family_tags(interface_family)
    motivating_task_ids = sorted({
        task_id
        for tag in benchmark_tags
        for task_id in task_ids_by_tag.get(tag, [])
    })
    family_benchmark_task_ids = sorted({
        task_id
        for tag in family_tags
        for task_id in task_ids_by_tag.get(tag, [])
    })
    return {
        "target_id": str(spec["target_id"]),
        "interface_family": interface_family,
        "status": str(spec["status"]),
        "lean_module": str(spec["lean_module"]),
        "lean_declarations": [
            str(declaration)
            for declaration in _sequence(spec.get("lean_declarations"))
        ],
        "depends_on": [
            str(dependency)
            for dependency in _sequence(spec.get("depends_on"))
        ],
        "benchmark_tags": list(benchmark_tags),
        "motivating_task_ids": motivating_task_ids,
        "family_benchmark_task_ids": family_benchmark_task_ids,
        "next_lemma_candidates": [
            str(candidate)
            for candidate in _sequence(spec.get("next_lemma_candidates"))
        ],
        "gate_status": (
            "ready_for_lemma_targets"
            if family_benchmark_task_ids
            else "needs_benchmark_seed"
        ),
    }


def _empirical_process_family_tags(interface_family: str) -> tuple[str, ...]:
    if interface_family == "bracketing":
        return ("bracketing_number",)
    if interface_family == "vc_subgraph":
        return ("vc_subgraph",)
    return (interface_family,)


def _external_baseline_row(
    spec: Mapping[str, object],
    *,
    split: str,
    benchmark_path: str,
    output_dir: str,
    task_count: int,
) -> dict[str, object]:
    baseline_id = str(spec["baseline_id"])
    attempts_path = f"{output_dir}/{baseline_id}-{split}-attempts.jsonl"
    reports_path = f"{output_dir}/{baseline_id}-{split}-reports.jsonl"
    summary_path = f"{output_dir}/{baseline_id}-{split}-summary.json"
    command_template = str(spec["command_template"])
    return {
        "baseline_id": baseline_id,
        "display_name": str(spec["display_name"]),
        "runner_type": str(spec["runner_type"]),
        "status": str(spec["status"]),
        "requires": [str(requirement) for requirement in _sequence(spec.get("requires"))],
        "target_task_count": task_count,
        "attempts_path": attempts_path,
        "reports_path": reports_path,
        "summary_path": summary_path,
        "command": command_template.format(
            benchmarks=benchmark_path,
            split=split,
            attempts=attempts_path,
            reports=reports_path,
            summary=summary_path,
        ),
    }


def _external_baseline_result_row(
    tasks: tuple[BenchmarkTask, ...],
    baseline: Mapping[str, object],
    *,
    split: str,
    attempts: tuple[ProofAttempt, ...] | None,
    reports: tuple[VerificationReport, ...] | None,
    source: str,
    selected_tasks: tuple[BenchmarkTask, ...] | None = None,
    comparison_id: str | None = None,
) -> dict[str, object]:
    baseline_id = str(baseline.get("baseline_id", ""))
    base_row = {
        "baseline_id": baseline_id,
        "display_name": str(baseline.get("display_name", "")),
        "runner_type": str(baseline.get("runner_type", "")),
        "planned_status": str(baseline.get("status", "")),
        "source": source,
        "attempts_path": str(baseline.get("attempts_path", "")),
        "reports_path": str(baseline.get("reports_path", "")),
        "summary_path": str(baseline.get("summary_path", "")),
        "target_task_count": int(baseline.get("target_task_count", 0)),
    }
    if attempts is None or reports is None:
        missing = []
        if attempts is None:
            missing.append(str(baseline.get("attempts_path", "")))
        if reports is None:
            missing.append(str(baseline.get("reports_path", "")))
        planned_status = str(baseline.get("status", ""))
        ingestion_status = (
            "blocked_missing_results"
            if planned_status == "ready"
            else "blocked_by_plan_status"
        )
        return {
            **base_row,
            "ingestion_status": ingestion_status,
            "evaluated_task_count": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "mean_reward": 0.0,
            "mean_premise_recall": 0.0,
            "status_counts": _empty_status_counts(),
            "failure_categories": {},
            "blocked_reasons": [
                *(str(requirement) for requirement in _sequence(baseline.get("requires"))),
                *(f"missing result file: {path}" for path in missing if path),
            ],
        }

    try:
        if selected_tasks is None:
            comparison = compare_baseline_on_split(
                tasks,
                attempts,
                reports,
                baseline=baseline_id,
                split=split,
            )
        else:
            comparison = _compare_baseline_on_tasks(
                tasks,
                attempts,
                reports,
                baseline=baseline_id,
                selected_tasks=selected_tasks,
                comparison_id=comparison_id or f"{baseline_id}::{split}",
                split_label=split,
            )
    except ValueError as error:
        return {
            **base_row,
            "ingestion_status": "ingestion_error",
            "evaluated_task_count": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "mean_reward": 0.0,
            "mean_premise_recall": 0.0,
            "status_counts": _empty_status_counts(),
            "failure_categories": {},
            "blocked_reasons": [str(error)],
        }

    return {
        **base_row,
        "ingestion_status": "ingested",
        "evaluated_task_count": int(comparison["benchmark_task_count"]),
        "passed": int(comparison["passed"]),
        "failed": int(comparison["failed"]),
        "pass_rate": float(comparison["pass_rate"]),
        "mean_reward": float(comparison["mean_reward"]),
        "mean_premise_recall": float(comparison["mean_premise_recall"]),
        "status_counts": dict(_mapping(comparison["status_counts"])),
        "failure_categories": dict(_mapping(comparison["failure_categories"])),
        "blocked_reasons": [],
    }


def _empirical_process_external_family_row(
    target: Mapping[str, object],
    task_by_id: Mapping[str, BenchmarkTask],
    seed_attempts: tuple[ProofAttempt, ...],
    seed_reports: tuple[VerificationReport, ...],
) -> dict[str, object]:
    task_ids = tuple(str(task_id) for task_id in _sequence(target.get("family_benchmark_task_ids")))
    known_task_ids = tuple(task_id for task_id in task_ids if task_id in task_by_id)
    missing_task_ids = tuple(task_id for task_id in task_ids if task_id not in task_by_id)
    family_tasks = tuple(task_by_id[task_id] for task_id in known_task_ids)

    seed_pass_rate = 0.0
    seed_passed = 0
    seed_status = "missing_seed_registry_evidence"
    if seed_attempts and seed_reports and family_tasks:
        try:
            comparison = _compare_baseline_on_tasks(
                tuple(task_by_id.values()),
                seed_attempts,
                seed_reports,
                baseline="seed-registry",
                selected_tasks=family_tasks,
                comparison_id=f"seed-registry::{target.get('interface_family', '')}",
                split_label=str(target.get("interface_family", "")),
            )
            seed_passed = int(comparison["passed"])
            seed_pass_rate = float(comparison["pass_rate"])
            seed_status = "verified" if seed_passed == len(family_tasks) else "partial"
        except ValueError as error:
            seed_status = f"error: {error}"

    return {
        "target_id": str(target.get("target_id", "")),
        "interface_family": str(target.get("interface_family", "")),
        "gate_status": str(target.get("gate_status", "")),
        "task_count": len(family_tasks),
        "task_ids": list(known_task_ids),
        "missing_task_ids": list(missing_task_ids),
        "seed_registry_status": seed_status,
        "seed_registry_passed": seed_passed,
        "seed_registry_pass_rate": seed_pass_rate,
    }


def _vdvw_inventory_row(
    spec: Mapping[str, object],
    task_by_id: Mapping[str, BenchmarkTask],
    *,
    markdown_root: str,
) -> dict[str, object]:
    benchmark_task_ids = tuple(str(task_id) for task_id in _sequence(spec.get("benchmark_task_ids")))
    present_task_ids = tuple(task_id for task_id in benchmark_task_ids if task_id in task_by_id)
    missing_task_ids = tuple(task_id for task_id in benchmark_task_ids if task_id not in task_by_id)
    missing_definitions = tuple(str(item) for item in _sequence(spec.get("missing_definitions")))
    semantic_risks = tuple(str(item) for item in _sequence(spec.get("semantic_risks")))
    current_claim_level = str(spec.get("current_claim_level", ""))
    promotion_status = (
        "ready_for_statement_candidate"
        if not missing_definitions
        and not semantic_risks
        and current_claim_level in {"primitive_proof", "deterministic_reduction"}
        else "blocked_pending_primitives_or_review"
    )
    return {
        "inventory_id": str(spec["inventory_id"]),
        "source_label": str(spec["source_label"]),
        "kind": str(spec["kind"]),
        "title": str(spec["title"]),
        "chapter": str(spec["chapter"]),
        "markdown_anchor": {
            "root": markdown_root,
            "segment": str(spec["source_segment"]),
            "line_start": int(spec["source_line_start"]),
            "line_end": int(spec["source_line_end"]),
        },
        "textbook_paraphrase": str(spec["textbook_paraphrase"]),
        "interface_family": str(spec["interface_family"]),
        "formalization_tier": str(spec["formalization_tier"]),
        "current_claim_level": current_claim_level,
        "current_lean_declarations": [
            str(declaration)
            for declaration in _sequence(spec.get("current_lean_declarations"))
        ],
        "benchmark_task_ids": list(present_task_ids),
        "missing_benchmark_task_ids": list(missing_task_ids),
        "missing_definitions": list(missing_definitions),
        "semantic_risks": list(semantic_risks),
        "next_actions": [
            str(action)
            for action in _sequence(spec.get("next_actions"))
        ],
        "promotion_status": promotion_status,
        "human_review_required": True,
    }


def _vdvw_statement_candidate_row(
    spec: Mapping[str, object],
    task_by_id: Mapping[str, BenchmarkTask],
) -> dict[str, object]:
    benchmark_task_ids = tuple(str(task_id) for task_id in _sequence(spec.get("benchmark_task_ids")))
    present_task_ids = tuple(task_id for task_id in benchmark_task_ids if task_id in task_by_id)
    missing_task_ids = tuple(task_id for task_id in benchmark_task_ids if task_id not in task_by_id)
    return {
        "candidate_id": str(spec["candidate_id"]),
        "track": str(spec["track"]),
        "status": str(spec["status"]),
        "statement_kind": str(spec["statement_kind"]),
        "target_lean_names": [
            str(name)
            for name in _sequence(spec.get("target_lean_names"))
        ],
        "formal_statement_sketch": str(spec["formal_statement_sketch"]),
        "required_primitives": [
            str(item)
            for item in _sequence(spec.get("required_primitives"))
        ],
        "proof_obligations": [
            str(item)
            for item in _sequence(spec.get("proof_obligations"))
        ],
        "existing_lean_handoffs": [
            str(item)
            for item in _sequence(spec.get("existing_lean_handoffs"))
        ],
        "benchmark_task_ids": list(present_task_ids),
        "missing_benchmark_task_ids": list(missing_task_ids),
        "local_lake_validation_hooks": [
            str(item)
            for item in _sequence(spec.get("local_lake_validation_hooks"))
        ],
        "axle_validation_hooks": [
            str(item)
            for item in _sequence(spec.get("axle_validation_hooks"))
        ],
        "semantic_risks": [
            str(item)
            for item in _sequence(spec.get("semantic_risks"))
        ],
        "promotion_gate": str(spec["promotion_gate"]),
        "human_review_required": True,
    }


def _vdvw_proof_obligation_row(
    spec: Mapping[str, object],
    task_by_id: Mapping[str, BenchmarkTask],
) -> dict[str, object]:
    benchmark_task_ids = tuple(str(task_id) for task_id in _sequence(spec.get("benchmark_task_ids")))
    present_task_ids = tuple(task_id for task_id in benchmark_task_ids if task_id in task_by_id)
    missing_task_ids = tuple(task_id for task_id in benchmark_task_ids if task_id not in task_by_id)
    return {
        "obligation_id": str(spec["obligation_id"]),
        "source_label": str(spec["source_label"]),
        "track": str(spec["track"]),
        "status": str(spec["status"]),
        "target_lean_names": [
            str(name)
            for name in _sequence(spec.get("target_lean_names"))
        ],
        "formal_goal": str(spec["formal_goal"]),
        "required_primitives": [
            str(item)
            for item in _sequence(spec.get("required_primitives"))
        ],
        "proof_obligations": [
            str(item)
            for item in _sequence(spec.get("proof_obligations"))
        ],
        "current_lean_handoffs": [
            str(item)
            for item in _sequence(spec.get("current_lean_handoffs"))
        ],
        "benchmark_task_ids": list(present_task_ids),
        "missing_benchmark_task_ids": list(missing_task_ids),
        "validation_hooks": [
            str(item)
            for item in _sequence(spec.get("validation_hooks"))
        ],
        "semantic_risks": [
            str(item)
            for item in _sequence(spec.get("semantic_risks"))
        ],
        "promotion_gate": str(spec["promotion_gate"]),
        "human_review_required": True,
    }


def _vdvw_primitive_semantics_row(
    spec: Mapping[str, object],
    task_by_id: Mapping[str, BenchmarkTask],
) -> dict[str, object]:
    existing_benchmark_task_ids = tuple(
        str(task_id) for task_id in _sequence(spec.get("existing_benchmark_task_ids"))
    )
    present_task_ids = tuple(
        task_id for task_id in existing_benchmark_task_ids if task_id in task_by_id
    )
    missing_task_ids = tuple(
        task_id for task_id in existing_benchmark_task_ids if task_id not in task_by_id
    )
    return {
        "primitive_id": str(spec["primitive_id"]),
        "layer": str(spec["layer"]),
        "status": str(spec["status"]),
        "source_anchor_ids": [
            str(anchor_id)
            for anchor_id in _sequence(spec.get("source_anchor_ids"))
        ],
        "target_lean_module": str(spec["target_lean_module"]),
        "target_lean_signatures": [
            str(signature)
            for signature in _sequence(spec.get("target_lean_signatures"))
        ],
        "current_lean_handoffs": [
            str(handoff)
            for handoff in _sequence(spec.get("current_lean_handoffs"))
        ],
        "theorem_card_gaps": [
            str(gap)
            for gap in _sequence(spec.get("theorem_card_gaps"))
        ],
        "existing_benchmark_task_ids": list(present_task_ids),
        "missing_existing_benchmark_task_ids": list(missing_task_ids),
        "planned_theorem_hole_seed_ids": [
            str(seed_id)
            for seed_id in _sequence(spec.get("planned_theorem_hole_seed_ids"))
        ],
        "validation_hooks": [
            str(hook)
            for hook in _sequence(spec.get("validation_hooks"))
        ],
        "semantic_risks": [
            str(risk)
            for risk in _sequence(spec.get("semantic_risks"))
        ],
        "promotion_gate": str(spec["promotion_gate"]),
        "human_review_required": True,
    }


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _empty_status_counts() -> dict[str, int]:
    return {status.value: 0 for status in VerificationStatus}


def _normalize_status(
    status: VerificationStatus | str,
    task_id: str,
    diagnostics: list[str],
) -> VerificationStatus:
    if isinstance(status, VerificationStatus):
        return status

    normalized = str(status).strip().lower()
    for candidate in VerificationStatus:
        if normalized in {candidate.value, candidate.name.lower()}:
            return candidate

    diagnostics.append(f"{task_id}: unknown verification status `{status}` counted as error")
    return VerificationStatus.ERROR


def _premise_recall(expected: tuple[str, ...], used: tuple[str, ...]) -> float:
    if not expected:
        return 1.0
    used_set = set(used)
    return sum(1 for premise in expected if premise in used_set) / len(expected)
