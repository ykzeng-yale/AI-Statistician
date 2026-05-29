from __future__ import annotations

import asyncio
import json
import unittest
from pathlib import Path

from ai_statistician.algorithms import audit_algorithm_registry
from ai_statistician.capability_audit import build_capability_audit, write_capability_audit
from ai_statistician.doctor import build_doctor_report, write_doctor_manifest
from ai_statistician.frontier_coverage_audit import audit_frontier_coverage, load_frontier_benchmark_questions
from ai_statistician.frontier_precision_audit import audit_frontier_precision
from ai_statistician.frontier_smoke_benchmark import FrontierSmokeConfig, run_frontier_smoke_benchmark, select_supported_frontier_questions
from ai_statistician.formal_gap_task_export import export_formal_gap_lean_tasks
from ai_statistician.formalization_target_audit import audit_formalization_targets
from ai_statistician.formal_source_graph import FormalSourceGraphRetriever, audit_formal_source_graph
from ai_statistician.formal_source_index import (
    FormalSourceRoot,
    FormalSourceSqliteIndex,
    audit_formal_source_index,
    build_formal_source_index,
    search_formal_sources,
)
from ai_statistician.proof_bank import all_obligations, get_obligation
from ai_statistician.evaluation import EvalConfig, run_seed_eval
from ai_statistician.intake_audit import audit_question_intake
from ai_statistician.frontier_backlog_audit import audit_frontier_backlog
from ai_statistician.proof_audit import audit_proof_bank
from ai_statistician.proof_policy_baseline import evaluate_retrieval_proof_policy_baseline
from ai_statistician.proof_repair_export import export_proof_repair_dataset
from ai_statistician.proof_training_export import export_proof_training_dataset
from ai_statistician.prover_component_audit import build_prover_component_audit, write_prover_component_audit
from ai_statistician.questions import load_question_file, question_from_json
from ai_statistician.release import ReleaseBundleConfig, build_release_bundle
from ai_statistician.research_evaluation import ResearchEvalConfig, run_research_seed_eval
from ai_statistician.research_gap_audit import audit_research_gap_backlog
from ai_statistician.research_intake_audit import audit_research_question_intake
from ai_statistician.research_knowledge_audit import audit_research_knowledge
from ai_statistician.research_capability_audit import (
    build_research_capability_audit,
    write_research_capability_audit,
)
from ai_statistician.research_lab import (
    audit_research_algorithm_registry,
    load_open_research_questions,
    ProblemFormalizer,
    run_research_benchmark,
    TheoryPlanner,
)
from ai_statistician.research_next_iteration_audit import audit_next_iteration_queue
from ai_statistician.research_paper_index import build_paper_source_index, retrieve_paper_sources
from ai_statistician.research_report import build_research_markdown_report
from ai_statistician.research_system_audit import ResearchSystemAuditConfig, run_research_system_audit
from ai_statistician.research_trace_audit import audit_research_traces
from ai_statistician.research_trace_audit import DIAGNOSTIC_METRIC_ALIASES
from ai_statistician.retrieval import ProofBankRetriever, RetrievalQuery, audit_proof_bank_retrieval
from ai_statistician.system import AIStatisticianSystem
from ai_statistician.system import write_run_manifest, write_trace
from ai_statistician.system_audit import SystemAuditConfig, load_audit_questions, run_system_audit
from ai_statistician.theory_proposal import MockTheoryProposer, TheoryProposal
from ai_statistician.trace_audit import audit_run_traces
from ai_statistician.verifier import CachingProofVerifier, MockProofVerifier
from ai_statistician.verifier import splice_proof


class ProofBankTests(unittest.TestCase):
    def test_registered_proofs_splice_out_sorry(self) -> None:
        for obligation in all_obligations():
            content = splice_proof(obligation.formal_statement, obligation.proof_body)
            self.assertNotIn("by sorry", content, obligation.id)
            self.assertIn("theorem", content, obligation.id)

    def test_retriever_finds_indicator_obligation(self) -> None:
        retriever = ProofBankRetriever()
        hits = retriever.retrieve(
            RetrievalQuery("event indicator expectation Bernoulli probability", tags=("indicator", "probability")),
            candidates=all_obligations(),
        )
        self.assertTrue(hits)
        self.assertEqual(hits[0].obligation_id, "event_indicator_expectation")

    def test_retrieval_audit_recovers_proof_bank(self) -> None:
        payload = audit_proof_bank_retrieval(Path("runs/test_retrieval_audit"), k=5)
        self.assertTrue(payload["all_top_k"])
        self.assertGreaterEqual(payload["top1_rate"], 0.7)
        self.assertEqual(len(payload["proof_bank_fingerprint"]), 64)
        self.assertFalse(payload["loogle"]["enabled"])
        self.assertTrue(Path("runs/test_retrieval_audit/retrieval_audit_manifest.json").exists())

    def test_retrieval_audit_can_attach_external_loogle_evidence(self) -> None:
        class FakeLoogleRetriever:
            source = "fake-loogle"

            def search_names(self, query: str, k: int = 10) -> list[str]:
                return [
                    "MeasureTheory.integral_const",
                    "ProbabilityTheory.variance_nonneg",
                    "ProbabilityTheory.IndepFun.variance_add",
                ][:k]

        payload = audit_proof_bank_retrieval(
            Path("runs/test_retrieval_audit_loogle"),
            k=5,
            include_loogle=True,
            loogle_retriever=FakeLoogleRetriever(),
        )
        self.assertTrue(payload["all_top_k"])
        self.assertTrue(payload["loogle"]["enabled"])
        self.assertEqual(payload["loogle"]["source"], "fake-loogle")
        self.assertGreaterEqual(payload["loogle"]["n_expected_lemma_hits"], 3)
        self.assertEqual(payload["loogle"]["n_errors"], 0)
        self.assertTrue(Path("runs/test_retrieval_audit_loogle/retrieval_audit_manifest.json").exists())

    def test_formal_source_index_extracts_and_searches_local_lean_declarations(self) -> None:
        fixture = Path("runs/test_formal_source_fixture")
        fixture.mkdir(parents=True, exist_ok=True)
        (fixture / "Demo.lean").write_text(
            "\n".join(
                [
                    "import Mathlib",
                    "namespace Demo",
                    "lemma bonferroni_union_bound : True := by trivial",
                    "theorem variance_sum_indep",
                    "    (h_indep : IndepFun X Y μ) :",
                    "    variance (X + Y) μ = variance X μ + variance Y μ := by trivial",
                    "end Demo",
                ]
            ),
            encoding="utf-8",
        )
        root = FormalSourceRoot("fixture", str(fixture))
        declarations = build_formal_source_index(roots=(root,))
        names = {decl.name for decl in declarations}
        self.assertIn("Demo.bonferroni_union_bound", names)
        self.assertIn("Demo.variance_sum_indep", names)
        hits = search_formal_sources("Bonferroni finite union bound", declarations=declarations, k=3)
        self.assertTrue(hits)
        self.assertEqual(hits[0].declaration.name, "Demo.bonferroni_union_bound")
        variance_decl = next(decl for decl in declarations if decl.name == "Demo.variance_sum_indep")
        self.assertIn("IndepFun", variance_decl.premise_heads)
        self.assertEqual(variance_decl.lhs_head, "variance")
        self.assertIn("variance", variance_decl.major_symbols)
        shape_hits = search_formal_sources(
            "variance equality with IndepFun premise",
            declarations=declarations,
            k=3,
        )
        self.assertEqual(shape_hits[0].declaration.name, "Demo.variance_sum_indep")
        sqlite_index = FormalSourceSqliteIndex.build(
            declarations,
            Path("runs/test_formal_source_index/formal_source_index.sqlite"),
        )
        sqlite_hits = sqlite_index.search("variance equality IndepFun premise", k=3)
        self.assertTrue(sqlite_hits)
        self.assertEqual(sqlite_hits[0].declaration.name, "Demo.variance_sum_indep")
        self.assertEqual(len(sqlite_index.load_declarations()), 2)
        graph = FormalSourceGraphRetriever(declarations)
        graph_hits = graph.search("independent variance estimator", k=3)
        self.assertTrue(graph_hits)
        self.assertEqual(graph_hits[0].declaration.name, "Demo.variance_sum_indep")
        self.assertTrue(graph_hits[0].graph_symbols)
        graph_payload = audit_formal_source_graph(
            Path("runs/test_formal_source_graph"),
            declarations=declarations,
            queries=(("variance_graph", "independent variance estimator"),),
        )
        self.assertTrue(graph_payload["all_queries_ok"])
        self.assertGreater(graph_payload["n_symbol_nodes"], 0)
        self.assertTrue(Path("runs/test_formal_source_graph/formal_source_graph_manifest.json").exists())
        payload = audit_formal_source_index(
            Path("runs/test_formal_source_index"),
            roots=(root,),
            queries=(("bonferroni", "Bonferroni finite union bound"),),
        )
        self.assertTrue(payload["all_queries_ok"])
        self.assertEqual(payload["search_backend"], "sqlite_fts_hybrid")
        self.assertEqual(Path(payload["sqlite_index_path"]).name, "formal_source_index.sqlite")
        self.assertTrue(Path(payload["sqlite_index_path"]).exists())
        self.assertEqual(payload["n_declarations"], 2)
        self.assertTrue(Path("runs/test_formal_source_index/formal_source_index_manifest.json").exists())

    def test_mock_proof_bank_audit_exports_lean(self) -> None:
        async def run():
            return await audit_proof_bank(
                MockProofVerifier(),
                Path("runs/test_proof_audit"),
                ids=["event_indicator_expectation", "variance_nonneg"],
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_verified"])
        self.assertFalse(payload["all_kernel_verified"])
        self.assertEqual(payload["verification_strength"], "mock_static_check")
        self.assertEqual(payload["n_kernel_verified"], 0)
        self.assertEqual(payload["n_non_kernel_verified"], 2)
        self.assertEqual(len(payload["proof_bank_fingerprint"]), 64)
        manifest = Path("runs/test_proof_audit/proof_audit_manifest.json")
        lean_file = Path("runs/test_proof_audit/lean/event_indicator_expectation.lean")
        attempt_log = Path("runs/test_proof_audit/proof_attempts.jsonl")
        attempt_manifest = Path("runs/test_proof_audit/proof_attempt_log_manifest.json")
        self.assertTrue(manifest.exists())
        self.assertTrue(lean_file.exists())
        self.assertTrue(attempt_log.exists())
        self.assertTrue(attempt_manifest.exists())
        self.assertNotIn("by sorry", lean_file.read_text())
        self.assertEqual(payload["proof_attempt_log"]["n_attempts"], 2)
        self.assertEqual(payload["proof_attempt_log"]["n_positive"], 2)
        rows = [json.loads(line) for line in attempt_log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["schema_version"], 2)
        self.assertTrue(rows[0]["ok"])
        self.assertEqual(rows[0]["verification_strength"], "mock_static_check")
        self.assertFalse(rows[0]["kernel_verified"])
        self.assertEqual(rows[0]["reward"], 1.0)
        self.assertTrue(rows[0]["supervision_target"])
        self.assertTrue(rows[0]["candidate_hash"])
        self.assertIn("retrieval_hits", rows[0])
        training = export_proof_training_dataset(
            attempt_log,
            Path("runs/test_proof_training_export"),
            validation_fraction=0.5,
        )
        self.assertEqual(training["n_sft_examples"], 2)
        self.assertTrue(Path(training["train_jsonl"]).exists())
        self.assertTrue(Path(training["validation_jsonl"]).exists())
        self.assertTrue(Path(training["all_jsonl"]).exists())
        all_examples = [
            json.loads(line)
            for line in Path(training["all_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(all_examples), 2)
        self.assertEqual(all_examples[0]["task"], "lean_whole_proof_body")
        self.assertEqual(all_examples[0]["verification_strength"], "mock_static_check")
        self.assertFalse(all_examples[0]["kernel_verified"])
        self.assertIn("Formal statement:", all_examples[0]["prompt"])
        self.assertTrue(all_examples[0]["completion"])
        baseline = evaluate_retrieval_proof_policy_baseline(
            Path(training["train_jsonl"]),
            Path(training["validation_jsonl"]),
            Path("runs/test_proof_policy_baseline"),
            k=2,
        )
        self.assertEqual(baseline["n_train"] + baseline["n_validation"], 2)
        self.assertTrue(Path(baseline["predictions_jsonl"]).exists())
        self.assertIn("top1_exact_rate", baseline)

    def test_proof_repair_export_pairs_negative_controls(self) -> None:
        async def run():
            return await audit_proof_bank(
                MockProofVerifier(),
                Path("runs/test_proof_repair_audit"),
                ids=["event_indicator_expectation", "variance_nonneg"],
                include_negative_controls=True,
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_verified"])
        self.assertTrue(payload["negative_controls"]["enabled"])
        self.assertEqual(payload["proof_attempt_log"]["n_attempts"], 4)
        self.assertEqual(payload["proof_attempt_log"]["n_positive"], 2)
        self.assertEqual(payload["proof_attempt_log"]["n_negative"], 2)
        repair = export_proof_repair_dataset(
            Path("runs/test_proof_repair_audit/proof_attempts.jsonl"),
            Path("runs/test_proof_repair_export"),
            validation_fraction=0.0,
        )
        self.assertEqual(repair["n_negative_attempts"], 2)
        self.assertEqual(repair["n_repair_examples"], 2)
        self.assertEqual(repair["n_train"], 2)
        self.assertEqual(repair["n_validation"], 0)
        self.assertTrue(Path(repair["train_jsonl"]).exists())
        rows = [
            json.loads(line)
            for line in Path(repair["all_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["task"], "lean_whole_proof_repair_from_verifier_error")
        self.assertTrue(rows[0]["target_completion"])
        self.assertIn("Verifier errors", rows[0]["prompt"])

    def test_caching_verifier_reuses_checked_obligations(self) -> None:
        async def run():
            verifier = CachingProofVerifier(MockProofVerifier())
            obligation = get_obligation("prob_measure_univ")
            first = await verifier.verify(obligation, obligation.proof_body, [])
            second = await verifier.verify(obligation, obligation.proof_body, [])
            return verifier, first, second

        verifier, first, second = asyncio.run(run())
        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertEqual(verifier.cache_info(), {"hits": 1, "misses": 1, "size": 1})

    def test_proof_audit_records_dependency_graph(self) -> None:
        async def run():
            return await audit_proof_bank(
                MockProofVerifier(),
                Path("runs/test_proof_dependency_audit"),
                ids=[
                    "mean2_estimator_expectation",
                    "variance_indep_add",
                    "mean2_estimator_variance_indep",
                    "finite_sample_mean_unbiased",
                    "finite_sample_mean_variance_indep",
                    "estimator_error_chebyshev",
                    "block_estimator_chebyshev_bound",
                    "finite_union_bound",
                    "finite_horizon_type1_union_control",
                    "mean2_estimator_chebyshev_indep",
                    "finite_sample_mean_chebyshev_indep",
                ],
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_verified"])
        graph = payload["dependency_graph"]
        self.assertTrue(graph["all_ok"])
        self.assertGreaterEqual(graph["n_edges"], 4)
        rows = {row["obligation_id"]: row for row in graph["rows"]}
        self.assertEqual(
            rows["mean2_estimator_chebyshev_indep"]["depends_on"],
            [
                "mean2_estimator_expectation",
                "mean2_estimator_variance_indep",
                "estimator_error_chebyshev",
            ],
        )
        self.assertEqual(
            rows["finite_sample_mean_chebyshev_indep"]["depends_on"],
            [
                "finite_sample_mean_unbiased",
                "finite_sample_mean_variance_indep",
                "estimator_error_chebyshev",
            ],
        )
        self.assertEqual(
            rows["block_estimator_chebyshev_bound"]["depends_on"],
            ["estimator_error_chebyshev"],
        )
        self.assertEqual(
            rows["finite_horizon_type1_union_control"]["depends_on"],
            ["finite_union_bound"],
        )

    def test_finite_sample_mean_obligation_defines_estimator(self) -> None:
        obligation = get_obligation("finite_sample_mean_unbiased")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("def finMeanEstimator", content)
        self.assertIn("Fin n", content)
        self.assertIn("theorem finMeanEstimator_unbiased", content)
        self.assertIn("integral_finset_sum", content)
        self.assertNotIn("by sorry", content)

    def test_finite_sample_mean_variance_obligation_uses_variance_sum(self) -> None:
        obligation = get_obligation("finite_sample_mean_variance_indep")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("variance_indep_add",))
        self.assertIn("def finMeanEstimator", content)
        self.assertIn("theorem finMeanEstimator_variance_indep", content)
        self.assertIn("Set.Pairwise", content)
        self.assertIn("variance (finMeanEstimator X) μ", content)
        self.assertIn("(∑ i, variance (X i) μ) / (n : ℝ) ^ 2", content)
        self.assertIn("IndepFun.variance_sum", content)
        self.assertIn("variance_smul", content)
        self.assertNotIn("by sorry", content)

    def test_finite_sample_mean_chebyshev_composes_mean_variance_and_tail_bound(self) -> None:
        obligation = get_obligation("finite_sample_mean_chebyshev_indep")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "finite_sample_mean_unbiased",
                "finite_sample_mean_variance_indep",
                "estimator_error_chebyshev",
            ),
        )
        self.assertIn("theorem finMeanEstimator_chebyshev_indep", content)
        self.assertIn("Set.Pairwise", content)
        self.assertIn("μ {ω | c ≤ |finMeanEstimator X ω - theta|}", content)
        self.assertIn("IndepFun.variance_sum", content)
        self.assertIn("meas_ge_le_variance_div_sq", content)
        self.assertNotIn("by sorry", content)

    def test_block_estimator_chebyshev_bridge_supports_robust_mean_gap(self) -> None:
        obligation = get_obligation("block_estimator_chebyshev_bound")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("estimator_error_chebyshev",))
        self.assertIn("robust", obligation.tags)
        self.assertIn("median_of_means", obligation.tags)
        self.assertIn("theorem blockEstimator_error_chebyshev", content)
        self.assertIn("μ {ω | c ≤ |B ω - theta|}", content)
        self.assertIn("meas_ge_le_variance_div_sq", content)
        self.assertNotIn("by sorry", content)

    def test_finite_horizon_type1_union_control_supports_sequential_gap(self) -> None:
        obligation = get_obligation("finite_horizon_type1_union_control")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("finite_union_bound",))
        self.assertIn("sequential", obligation.tags)
        self.assertIn("optional_stopping", obligation.tags)
        self.assertIn("theorem finiteHorizon_type1_union_control", content)
        self.assertIn("μ (⋃ i ∈ I, A i)", content)
        self.assertIn("∑ i ∈ I, α i", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("Finset.sum_le_sum", content)
        self.assertNotIn("by sorry", content)

    def test_affine_estimator_obligation_supports_shrinkage_expectation(self) -> None:
        obligation = get_obligation("affine_estimator_expectation")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("def affineEstimator", content)
        self.assertIn("theorem affineEstimator_expectation", content)
        self.assertIn("a * (∫ ω, X ω ∂μ) + b", content)
        self.assertIn("integral_const_mul", content)
        self.assertNotIn("by sorry", content)

    def test_affine_estimator_variance_supports_shrinkage_se(self) -> None:
        obligation = get_obligation("affine_estimator_variance")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("def affineEstimator", content)
        self.assertIn("theorem affineEstimator_variance", content)
        self.assertIn("a ^ 2 * variance X μ", content)
        self.assertIn("variance_add_const", content)
        self.assertIn("variance_const_mul", content)
        self.assertNotIn("by sorry", content)

    def test_mean2_variance_obligation_is_performance_guarantee(self) -> None:
        obligation = get_obligation("mean2_estimator_variance_indep")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("def mean2Estimator", content)
        self.assertIn("theorem mean2Estimator_variance_indep", content)
        self.assertIn("variance (mean2Estimator X Y) μ", content)
        self.assertIn("IndepFun X Y μ", content)
        self.assertIn("IndepFun.variance_add", content)
        self.assertIn("variance_smul", content)
        self.assertNotIn("by sorry", content)

    def test_chebyshev_obligation_is_estimator_error_bound(self) -> None:
        obligation = get_obligation("estimator_error_chebyshev")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem estimator_error_chebyshev", content)
        self.assertIn("MemLp X 2 μ", content)
        self.assertIn("μ[X] = theta", content)
        self.assertIn("μ {ω | c ≤ |X ω - theta|}", content)
        self.assertIn("variance X μ / c ^ 2", content)
        self.assertIn("meas_ge_le_variance_div_sq", content)
        self.assertNotIn("by sorry", content)

    def test_finite_union_bound_obligation_uses_mathlib_bonferroni_lemma(self) -> None:
        obligation = get_obligation("finite_union_bound")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem finite_union_bound", content)
        self.assertIn("μ (⋃ i ∈ I, A i)", content)
        self.assertIn("∑ i ∈ I, μ (A i)", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertNotIn("by sorry", content)

    def test_event_probability_mono_obligation_uses_measure_mono(self) -> None:
        obligation = get_obligation("event_probability_mono")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem event_probability_mono", content)
        self.assertIn("A ⊆ B", content)
        self.assertIn("μ A ≤ μ B", content)
        self.assertIn("measure_mono", content)
        self.assertNotIn("by sorry", content)

    def test_independent_event_inter_probability_uses_indep_set_measure_inter(self) -> None:
        obligation = get_obligation("independent_event_inter_probability")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem independent_event_inter_probability", content)
        self.assertIn("IndepSet A B μ", content)
        self.assertIn("μ (A ∩ B) = μ A * μ B", content)
        self.assertIn("IndepSet.measure_inter_eq_mul", content)
        self.assertNotIn("by sorry", content)

    def test_first_borel_cantelli_obligation_uses_mathlib_limsup_lemma(self) -> None:
        obligation = get_obligation("first_borel_cantelli_limsup_zero")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem first_borel_cantelli_limsup_zero", content)
        self.assertIn("(∑' n, μ (A n)) ≠ ∞", content)
        self.assertIn("μ (limsup A atTop) = 0", content)
        self.assertIn("MeasureTheory.measure_limsup_atTop_eq_zero", content)
        self.assertNotIn("by sorry", content)

    def test_second_borel_cantelli_obligation_uses_mathlib_independent_limsup_lemma(self) -> None:
        obligation = get_obligation("second_borel_cantelli_limsup_one")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem second_borel_cantelli_limsup_one", content)
        self.assertIn("iIndepSet A μ", content)
        self.assertIn("(∑' n, μ (A n)) = ∞", content)
        self.assertIn("μ (limsup A atTop) = 1", content)
        self.assertIn("ProbabilityTheory.measure_limsup_eq_one", content)
        self.assertNotIn("by sorry", content)

    def test_adapted_hitting_after_obligation_uses_mathlib_stopping_time_lemma(self) -> None:
        obligation = get_obligation("adapted_hitting_after_is_stopping_time")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem adapted_hitting_after_is_stopping_time", content)
        self.assertIn("Adapted ℱ X", content)
        self.assertIn("IsStoppingTime ℱ (hittingAfter X S n)", content)
        self.assertIn("hX.isStoppingTime_hittingAfter hS", content)
        self.assertNotIn("by sorry", content)

    def test_mean2_chebyshev_obligation_composes_unbiased_variance_bound(self) -> None:
        obligation = get_obligation("mean2_estimator_chebyshev_indep")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "mean2_estimator_expectation",
                "mean2_estimator_variance_indep",
                "estimator_error_chebyshev",
            ),
        )
        self.assertIn("theorem mean2Estimator_chebyshev_indep", content)
        self.assertIn("hEX : μ[X] = theta", content)
        self.assertIn("hEY : μ[Y] = theta", content)
        self.assertIn("IndepFun X Y μ", content)
        self.assertIn("((variance X μ + variance Y μ) / 4) / c ^ 2", content)
        self.assertIn("IndepFun.variance_add", content)
        self.assertIn("meas_ge_le_variance_div_sq", content)
        self.assertNotIn("by sorry", content)

    def test_finite_event_indicator_mean_obligation_defines_sample_proportion(self) -> None:
        obligation = get_obligation("finite_event_indicator_mean_unbiased")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("def eventIndicator", content)
        self.assertIn("def finMeanEstimator", content)
        self.assertIn("theorem finiteEventIndicatorMean_unbiased", content)
        self.assertIn("integral_indicator_const", content)
        self.assertIn("integral_finset_sum", content)
        self.assertNotIn("by sorry", content)

    def test_noised_estimator_obligations_bridge_private_mean_error(self) -> None:
        unbiased = get_obligation("noised_estimator_unbiased")
        variance = get_obligation("noised_estimator_variance_indep")
        chebyshev = get_obligation("noised_estimator_chebyshev_indep")
        content = splice_proof(chebyshev.formal_statement, chebyshev.proof_body)
        self.assertEqual(
            chebyshev.depends_on,
            (
                "noised_estimator_unbiased",
                "noised_estimator_variance_indep",
                "estimator_error_chebyshev",
            ),
        )
        self.assertIn("def noisedEstimator", splice_proof(unbiased.formal_statement, unbiased.proof_body))
        self.assertIn("IndepFun.variance_add", splice_proof(variance.formal_statement, variance.proof_body))
        self.assertIn("theorem noisedEstimator_chebyshev_indep", content)
        self.assertIn("variance X μ + variance Z μ", content)
        self.assertIn("meas_ge_le_variance_div_sq", content)
        self.assertNotIn("by sorry", content)


class SystemTests(unittest.TestCase):
    def test_algorithm_registry_audit_passes(self) -> None:
        payload = audit_algorithm_registry(Path("runs/test_algorithm_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_ok"], payload["n_algorithms"])
        self.assertEqual(len(payload["registry_fingerprint"]), 64)
        self.assertTrue(Path("runs/test_algorithm_audit/algorithm_audit_manifest.json").exists())

    def test_research_algorithm_registry_audit_passes(self) -> None:
        payload = audit_research_algorithm_registry(Path("runs/test_research_algorithm_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_ok"], payload["n_algorithms"])
        self.assertEqual(payload["n_algorithms"], 14)
        self.assertEqual(len(payload["registry_fingerprint"]), 64)
        for row in payload["algorithms"]:
            self.assertEqual(row["registry_status"], "vetted")
            self.assertEqual(len(row["implementation_hash"]), 64)
        self.assertTrue(Path("runs/test_research_algorithm_audit/research_algorithm_audit_manifest.json").exists())

    def test_research_intake_audit_accepts_supported_and_rejects_unsupported(self) -> None:
        payload = audit_research_question_intake(Path("runs/test_research_intake_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_supported"], 20)
        self.assertEqual(payload["n_supported_accepted"], 20)
        self.assertEqual(payload["n_unsupported"], 4)
        self.assertEqual(payload["n_unsupported_rejected"], 4)
        self.assertEqual(
            set(payload["supported_problem_classes"]),
            {
                "semiparametric_causal_ate",
                "distribution_free_conformal_prediction",
                "right_censored_survival_inference",
                "robust_mean_inference",
                "design_based_variance_inference",
                "heteroskedastic_regression_inference",
                "multiple_testing_fdr",
                "sequential_anytime_inference",
                "high_dimensional_pca_inference",
                "extreme_tail_quantile_inference",
            },
        )
        self.assertTrue(Path("runs/test_research_intake_audit/research_intake_audit_manifest.json").exists())

    def test_research_knowledge_audit_checks_sources_and_problem_retrieval(self) -> None:
        payload = audit_research_knowledge(Path("runs/test_research_knowledge_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_cards"], payload["n_source_ok"])
        self.assertTrue(payload["source_inventory"]["all_ok"])
        self.assertEqual(payload["source_inventory"]["n_ok"], payload["source_inventory"]["n_sources"])
        self.assertEqual(len(payload["source_inventory"]["inventory_fingerprint"]), 64)
        self.assertEqual(payload["n_problem_rows"], 10)
        self.assertEqual(payload["n_problem_ok"], 10)
        self.assertFalse(payload["duplicate_ids"])
        for row in payload["problem_rows"]:
            self.assertTrue(row["has_primary"])
            self.assertTrue(row["has_method_card"])
            self.assertTrue(row["has_formal_infra"])
            self.assertTrue(row["has_local_formal_source"])
            self.assertTrue(row["has_search_infra"])
            self.assertEqual(row["top_hit"], row["expected_primary"])
        self.assertTrue(Path("runs/test_research_knowledge_audit/research_knowledge_audit_manifest.json").exists())
        self.assertTrue(Path("runs/test_research_knowledge_audit/research_knowledge_audit.md").exists())
        self.assertTrue(
            Path("runs/test_research_knowledge_audit/source_inventory/research_source_inventory_manifest.json").exists()
        )

    def test_frontier_coverage_audit_parses_paper_benchmark(self) -> None:
        questions = load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
        self.assertEqual(len(questions), 60)
        self.assertTrue(all(question.open_question for question in questions))
        self.assertTrue(all(question.expected_results for question in questions))
        open_question = questions[0].to_open_research_question()
        self.assertNotIn("Expected theoretical results", open_question.description)
        for expected in questions[0].expected_results:
            self.assertNotIn(expected, open_question.description)

        payload = audit_frontier_coverage(Path("runs/test_frontier_coverage_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_questions"], 60)
        self.assertGreater(payload["n_supported"], 0)
        self.assertGreater(payload["n_unsupported"], 0)
        self.assertIn("unsupported_frontier_question", payload["by_problem_class"])
        self.assertTrue(Path("runs/test_frontier_coverage_audit/frontier_coverage_manifest.json").exists())
        self.assertTrue(Path("runs/test_frontier_coverage_audit/frontier_coverage.md").exists())

    def test_frontier_precision_audit_requires_body_evidence(self) -> None:
        payload = audit_frontier_precision(Path("runs/test_frontier_precision_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_ok"], payload["n_supported"])
        self.assertEqual(payload["n_flagged"], 0)
        self.assertGreater(payload["n_supported"], 0)
        by_id = {row["question_id"]: row for row in payload["rows"]}
        self.assertIn("experimental_design_02", by_id)
        self.assertEqual(by_id["experimental_design_02"]["problem_class"], "design_based_variance_inference")
        self.assertTrue(by_id["experimental_design_02"]["evidence_terms"])
        self.assertIn("missing_censored_measurement_error_01", by_id)
        self.assertEqual(
            by_id["missing_censored_measurement_error_01"]["problem_class"],
            "measurement_bias_ranking_inference",
        )
        self.assertTrue(by_id["missing_censored_measurement_error_01"]["evidence_terms"])
        self.assertTrue(Path("runs/test_frontier_precision_audit/frontier_precision_manifest.json").exists())
        self.assertTrue(Path("runs/test_frontier_precision_audit/frontier_precision.md").exists())

    def test_frontier_backlog_audit_maps_unsupported_questions(self) -> None:
        payload = audit_frontier_backlog(Path("runs/test_frontier_backlog_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_backlog"], 33)
        self.assertEqual(payload["n_ok"], payload["n_backlog"])
        self.assertGreaterEqual(payload["n_supported"], 1)
        self.assertGreaterEqual(len(payload["by_domain"]), 6)
        self.assertTrue(payload["by_required_primitive"])
        by_id = {row["question_id"]: row for row in payload["rows"]}
        self.assertEqual(
            by_id["statistical_learning_nonparametric_02"]["roadmap_domain"],
            "statistical_learning_nonparametric",
        )
        self.assertEqual(
            by_id["networks_graphs_01"]["roadmap_domain"],
            "network_graph_dependence",
        )
        for row in payload["rows"]:
            self.assertTrue(row["required_primitives"])
            self.assertTrue(row["likely_methods"])
            self.assertFalse(row["errors"])
        self.assertTrue(Path("runs/test_frontier_backlog_audit/frontier_backlog_manifest.json").exists())
        self.assertTrue(Path("runs/test_frontier_backlog_audit/frontier_backlog.md").exists())

    def test_frontier_smoke_benchmark_runs_selected_supported_papers(self) -> None:
        selected, metadata = select_supported_frontier_questions(max_per_class=1)
        self.assertGreaterEqual(len(selected), 3)
        self.assertEqual(len(selected), len(metadata))
        self.assertEqual(len({row.problem_class for row in metadata}), len(metadata))

        async def run():
            return await run_frontier_smoke_benchmark(
                Path("runs/test_frontier_smoke_benchmark"),
                config=FrontierSmokeConfig(n_runs=25, seed=20260528),
                proof_verifier=MockProofVerifier(),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_gates_passed"])
        self.assertTrue(payload["gates"]["frontier_theory_target_audit"])
        self.assertEqual(payload["counts"]["questions"], payload["n_selected"])
        self.assertEqual(payload["counts"]["ready_with_gaps"], payload["n_selected"])
        self.assertEqual(payload["counts"]["traces_ok"], payload["n_selected"])
        self.assertEqual(payload["counts"]["theory_targets_scored"], payload["n_selected"])
        self.assertEqual(payload["counts"]["theory_targets_total"], payload["n_selected"])
        self.assertGreater(payload["counts"]["theory_expected_results"], 0)
        self.assertTrue(Path("runs/test_frontier_smoke_benchmark/frontier_smoke_manifest.json").exists())
        self.assertTrue(Path("runs/test_frontier_smoke_benchmark/selected_questions.json").exists())
        self.assertTrue(Path(payload["artifacts"]["research_benchmark"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_target_audit"]).exists())
        target_audit = json.loads(Path(payload["artifacts"]["frontier_theory_target_audit"]).read_text())
        self.assertTrue(target_audit["all_scored"])
        self.assertFalse(target_audit["limitations"][0] == "")
        dp_trace_path = Path("runs/test_frontier_smoke_benchmark/research_benchmark/robust_privacy_distributed_02.json")
        self.assertTrue(dp_trace_path.exists())
        dp_trace = json.loads(dp_trace_path.read_text())
        dp_goals = {row["id"]: row for row in dp_trace["theorem_goals"]}
        dp_support = dp_goals["private_mean_error_decomposition"]["proof_obligations"]
        self.assertEqual(
            dp_support,
            [
                "finite_sample_mean_variance_indep",
                "finite_sample_mean_chebyshev_indep",
                "noised_estimator_unbiased",
                "noised_estimator_variance_indep",
                "noised_estimator_chebyshev_indep",
            ],
        )
        dp_proved = {
            row["proof_obligation_id"]
            for row in dp_trace["formal_subclaims"]
            if row["status"] == "PROVED"
        }
        self.assertTrue(set(dp_support) <= dp_proved)

        bayes_trace_path = Path(
            "runs/test_frontier_smoke_benchmark/research_benchmark/bayesian_computation_posteriors_02.json"
        )
        self.assertTrue(bayes_trace_path.exists())
        bayes_trace = json.loads(bayes_trace_path.read_text())
        self.assertEqual(bayes_trace["problem"]["problem_class"], "bayesian_posterior_calibration")
        bayes_goals = {row["id"]: row for row in bayes_trace["theorem_goals"]}
        self.assertEqual(
            bayes_goals["normal_conjugate_posterior_mean_error_decomposition"]["proof_obligations"],
            [
                "affine_estimator_expectation",
                "affine_estimator_variance",
                "finite_sample_mean_unbiased",
                "finite_sample_mean_variance_indep",
                "finite_sample_mean_chebyshev_indep",
                "estimator_error_chebyshev",
                "variance_nonneg",
            ],
        )
        bayes_metrics = bayes_trace["simulations"][0]["metrics"]
        self.assertIn("posterior_sd", bayes_metrics)
        self.assertIn("prior_influence", bayes_metrics)

        measurement_trace_path = Path(
            "runs/test_frontier_smoke_benchmark/research_benchmark/missing_censored_measurement_error_01.json"
        )
        self.assertTrue(measurement_trace_path.exists())
        measurement_trace = json.loads(measurement_trace_path.read_text())
        self.assertEqual(
            measurement_trace["problem"]["problem_class"],
            "measurement_bias_ranking_inference",
        )
        measurement_goals = {row["id"]: row for row in measurement_trace["theorem_goals"]}
        self.assertEqual(
            measurement_goals["bias_adjusted_assessment_mean_identification"]["proof_obligations"],
            [
                "affine_estimator_expectation",
                "finite_sample_mean_unbiased",
                "integral_of_constant",
            ],
        )
        measurement_metrics = measurement_trace["simulations"][0]["metrics"]
        self.assertIn("rank_top1_accuracy", measurement_metrics)
        self.assertIn("rank_correlation", measurement_metrics)
        measurement_rank_support = measurement_goals["assessment_ranking_uncertainty_validity"][
            "proof_obligations"
        ]
        self.assertIn("affine_estimator_variance", measurement_rank_support)
        self.assertIn("finite_sample_mean_variance_indep", measurement_rank_support)

    def test_mock_system_accepts_registered_questions(self) -> None:
        async def run():
            system = AIStatisticianSystem(n_runs=200, seed=123)
            return await system.run_all()

        reports = asyncio.run(run())
        self.assertEqual({r.status for r in reports}, {"ACCEPTED"})
        for report in reports:
            self.assertTrue(all(p.ok for p in report.proofs))
            self.assertTrue(report.simulation.pass_bias)
            self.assertEqual(report.algorithm.registry_status, "vetted")
            self.assertEqual(len(report.algorithm.implementation_hash), 64)

    def test_external_question_file_runs_through_system(self) -> None:
        async def run():
            questions = load_question_file(Path("examples/questions.json"))
            system = AIStatisticianSystem(n_runs=200, seed=456)
            return [await system.run(question) for question in questions]

        reports = asyncio.run(run())
        self.assertEqual(len(reports), 3)
        self.assertEqual({r.status for r in reports}, {"ACCEPTED"})
        self.assertEqual(reports[0].estimator.question_id, "external_normal_mean")

        out_dir = Path("runs/test_manifest")
        for report in reports:
            write_trace(report, out_dir)
        manifest = write_run_manifest(reports, out_dir)
        self.assertTrue(manifest.exists())
        manifest_text = manifest.read_text()
        self.assertIn('"n_accepted": 3', manifest_text)
        self.assertIn('"provenance"', manifest_text)
        trace = json.loads(Path("runs/test_manifest/external_normal_mean.json").read_text())
        self.assertEqual(trace["trace_version"], 1)
        self.assertIn("provenance", trace)

    def test_trace_audit_validates_written_traces(self) -> None:
        async def run():
            questions = load_question_file(Path("examples/questions.json"))[:2]
            system = AIStatisticianSystem(n_runs=120, seed=789)
            reports = [await system.run(question) for question in questions]
            out_dir = Path("runs/test_trace_run")
            for report in reports:
                write_trace(report, out_dir)
            write_run_manifest(reports, out_dir)
            return audit_run_traces(out_dir, Path("runs/test_trace_audit"))

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_ok"], 2)
        self.assertEqual(payload["n_traces"], 2)
        self.assertTrue(Path("runs/test_trace_audit/trace_audit_manifest.json").exists())

    def test_custom_question_validation(self) -> None:
        with self.assertRaises(ValueError):
            question_from_json({"id": "bad"})

    def test_partial_question_file_infers_supported_families(self) -> None:
        questions = load_question_file(Path("examples/partial_questions.json"))
        self.assertEqual(
            [(q.dgp_family, q.estimator_family) for q in questions],
            [
                ("normal", "sample_mean"),
                ("bernoulli", "sample_proportion"),
                ("normal", "sample_variance"),
                ("constant", "constant_estimator"),
            ],
        )
        self.assertEqual(questions[0].true_params["mu"], 1.5)
        self.assertEqual(questions[1].true_params["p"], 0.42)
        self.assertEqual(questions[2].true_params["sigma"], 0.75)
        self.assertEqual(questions[3].true_params["c"], 2.25)

    def test_unsupported_question_is_rejected_before_simulation(self) -> None:
        with self.assertRaises(ValueError):
            question_from_json(
                {
                    "id": "unsupported_weibull",
                    "dgp": "X_i iid Weibull(shape=2.0, scale=1.0)",
                    "target": "Estimate the hazard ratio",
                    "n_obs": 100,
                }
            )

    def test_intake_audit_accepts_supported_and_rejects_unsupported(self) -> None:
        payload = audit_question_intake(Path("runs/test_intake_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_supported"], 7)
        self.assertEqual(payload["n_supported_accepted"], 7)
        self.assertEqual(payload["n_unsupported"], 3)
        self.assertEqual(payload["n_unsupported_rejected"], 3)
        self.assertTrue(Path("runs/test_intake_audit/intake_audit_manifest.json").exists())

    def test_llm_theory_proposer_can_classify_supported_question(self) -> None:
        proposer = MockTheoryProposer(
            TheoryProposal(
                dgp_family="bernoulli",
                estimator_family="sample_proportion",
                true_params={"p": 0.37},
                tags=("probability", "indicator"),
                confidence=0.92,
                source="mock-llm",
            )
        )
        question = question_from_json(
            {
                "id": "coin_success",
                "dgp": "Each observation is a coin-flip success indicator; the success chance p=0.37.",
                "target": "Estimate the chance of success.",
                "n_obs": 140,
            },
            theory_proposer=proposer,
        )
        self.assertEqual(question.dgp_family, "bernoulli")
        self.assertEqual(question.estimator_family, "sample_proportion")
        self.assertEqual(question.true_params["p"], 0.37)
        self.assertIn("theory_proposal:mock-llm", question.tags)

    def test_llm_theory_proposer_is_registry_gated(self) -> None:
        proposer = MockTheoryProposer(
            TheoryProposal(
                dgp_family="weibull",
                estimator_family="cox_model",
                true_params={"shape": 2.0},
                source="mock-llm",
            )
        )
        with self.assertRaises(ValueError):
            question_from_json(
                {
                    "id": "bad_llm",
                    "dgp": "Survival times follow a Weibull distribution.",
                    "target": "Estimate hazard ratio.",
                    "n_obs": 100,
                },
                theory_proposer=proposer,
            )

    def test_seed_eval_writes_aggregate_manifest(self) -> None:
        async def run():
            questions = load_question_file(Path("examples/questions.json"))[:1]
            return await run_seed_eval(
                questions,
                EvalConfig(seeds=(11, 12), n_runs=80),
                Path("runs/test_eval"),
            )

        payload = asyncio.run(run())
        row = payload["summary"]["external_normal_mean"]
        self.assertEqual(row["trials"], 2)
        self.assertEqual(row["accepted"], 2)
        self.assertTrue(Path("runs/test_eval/evaluation_manifest.json").exists())

    def test_system_audit_writes_release_manifest(self) -> None:
        async def run():
            questions = load_audit_questions(None, include_partial_examples=False)[:2]
            return await run_system_audit(
                Path("runs/test_system_audit"),
                questions=questions,
                config=SystemAuditConfig(n_runs=120, seeds=(31, 32), include_eval=True),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_gates_passed"])
        self.assertEqual(len(payload["provenance"]["proof_bank_fingerprint"]), 64)
        self.assertTrue(payload["gates"]["intake_audit"])
        self.assertTrue(payload["gates"]["algorithm_audit"])
        self.assertTrue(payload["gates"]["retrieval_audit"])
        self.assertTrue(payload["gates"]["proof_audit"])
        self.assertTrue(payload["gates"]["question_runs"])
        self.assertTrue(payload["gates"]["trace_audit"])
        self.assertTrue(payload["gates"]["evaluation"])
        self.assertEqual(payload["counts"]["intake_unsupported_rejected"], 3)
        self.assertEqual(payload["counts"]["traces_ok"], payload["counts"]["traces_total"])
        self.assertTrue(Path("runs/test_system_audit/system_audit_manifest.json").exists())

    def test_system_audit_can_skip_evaluation_gate(self) -> None:
        async def run():
            questions = load_audit_questions(None, include_partial_examples=False)[:1]
            return await run_system_audit(
                Path("runs/test_system_audit_no_eval"),
                questions=questions,
                config=SystemAuditConfig(n_runs=80, seeds=(41, 42), include_eval=False),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_gates_passed"])
        self.assertNotIn("evaluation", payload["gates"])
        self.assertIsNone(payload["artifacts"]["evaluation"])

    def test_doctor_report_is_redacted_and_manifested(self) -> None:
        report = build_doctor_report(
            root=Path("."),
            env_file=Path(".env"),
            environ={
                "AXLE_API_KEY": "do-not-print-axle",
                "ANTHROPIC_API_KEY": "do-not-print-anthropic",
            },
            max_manifests=3,
        )
        self.assertTrue(report["summary"]["required_ok"])
        self.assertEqual(report["summary"]["n_obligations"], len(all_obligations()))
        self.assertGreaterEqual(report["summary"]["n_algorithms"], 1)
        self.assertIn("real_lean_ready", report["summary"])
        self.assertIn("real_lean_blockers", report["summary"])
        self.assertIn("llm_theory_blockers", report["summary"])
        serialized = json.dumps(report)
        self.assertNotIn("do-not-print-axle", serialized)
        self.assertNotIn("do-not-print-anthropic", serialized)

        manifest = write_doctor_manifest(report, Path("runs/test_doctor"))
        self.assertTrue(manifest.exists())
        self.assertIn('"required_ok": true', manifest.read_text())

    def test_capability_audit_maps_objective_to_evidence(self) -> None:
        report = build_capability_audit(root=Path("."), max_manifests=3)
        self.assertTrue(report["all_required_capabilities_present"])
        self.assertGreaterEqual(report["n_ready"], 8)
        self.assertGreaterEqual(report["n_partial"], 0)
        findings = {row["requirement"]: row for row in report["findings"]}
        axle_row = findings["verify Mathlib-backed estimator/probability properties in Lean via AXLE"]
        self.assertIn(axle_row["status"], {"PARTIAL", "READY"})
        self.assertTrue(
            any("latest_proof_audit_kernel_verified=" in item for item in axle_row["evidence"])
        )
        self.assertTrue(
            any("latest_proof_audit_full_bank_kernel_verified=" in item for item in axle_row["evidence"])
        )
        self.assertIn("source_files", report)
        self.assertEqual(len(report["fingerprints"]["algorithm_registry"]), 64)

        manifest = write_capability_audit(report, Path("runs/test_capability_audit"))
        self.assertTrue(manifest.exists())
        self.assertEqual(manifest.name, "capability_audit_manifest.json")

    def test_release_bundle_writes_top_level_manifest(self) -> None:
        async def run():
            questions = load_audit_questions(None, include_partial_examples=False)[:2]
            return await build_release_bundle(
                Path("runs/test_release_bundle"),
                root=Path("."),
                questions=questions,
                config=ReleaseBundleConfig(n_runs=90, seeds=(51, 52), include_eval=False),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_release_gates_passed"])
        self.assertEqual(len(payload["release_id"]), 64)
        self.assertTrue(payload["gates"]["doctor_required"])
        self.assertTrue(payload["gates"]["capabilities_present"])
        self.assertTrue(payload["gates"]["system_audit"])
        self.assertEqual(len(payload["provenance"]["algorithm_registry_fingerprint"]), 64)
        self.assertTrue(Path("runs/test_release_bundle/release_manifest.json").exists())
        self.assertTrue(Path(payload["artifacts"]["doctor"]).exists())
        self.assertTrue(Path(payload["artifacts"]["capability_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["system_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["trace_audit"]).exists())

    def test_research_benchmark_writes_frontier_theory_traces(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))
            return await run_research_benchmark(
                questions,
                Path("runs/test_research_benchmark"),
                proof_verifier=MockProofVerifier(),
                formal_source_index_path=Path("runs/test_research_benchmark/formal_source_index.sqlite"),
                n_runs=25,
                seed=20260528,
            )

        payload = asyncio.run(run())
        self.assertEqual(payload["n_questions"], 10)
        self.assertEqual(payload["n_ready_with_gaps"], 10)
        self.assertEqual(payload["n_formal_blocked"], 0)
        self.assertEqual(payload["formal_source_search"]["backend"], "sqlite_fts_hybrid")
        self.assertTrue(Path(payload["formal_source_search"]["sqlite_index_path"]).exists())
        classes = {row["problem_class"] for row in payload["questions"]}
        self.assertEqual(
            classes,
            {
                "semiparametric_causal_ate",
                "distribution_free_conformal_prediction",
                "right_censored_survival_inference",
                "robust_mean_inference",
                "design_based_variance_inference",
                "heteroskedastic_regression_inference",
                "multiple_testing_fdr",
                "sequential_anytime_inference",
                "high_dimensional_pca_inference",
                "extreme_tail_quantile_inference",
            },
        )
        for row in payload["questions"]:
            self.assertGreaterEqual(row["formal"]["proved"], 2)
            self.assertGreaterEqual(row["formal"]["gaps"], 1)
            self.assertEqual(row["formal"]["formalized_gaps"], row["formal"]["gaps"])
            self.assertTrue(row["simulations"])
            self.assertTrue(all(sim["passed"] for sim in row["simulations"]))
        support_rows = [
            support
            for row in payload["questions"]
            for support in row["formal"]["theorem_goal_support"]
        ]
        self.assertGreaterEqual(len(support_rows), 9)
        for support in support_rows:
            self.assertEqual(support["n_proved_obligations"], len(support["proof_obligations"]))

        manifest = Path("runs/test_research_benchmark/research_benchmark_manifest.json")
        trace = Path("runs/test_research_benchmark/causal_ate_aipw.json")
        self.assertTrue(manifest.exists())
        self.assertTrue(trace.exists())
        trace_payload = json.loads(trace.read_text())
        self.assertEqual(trace_payload["trace_kind"], "research_theory_lab")
        self.assertIn("research_knowledge_fingerprint", trace_payload["provenance"])
        self.assertIn("paper_source_index_fingerprint", trace_payload["provenance"])
        self.assertIn("research_source_inventory_fingerprint", trace_payload["provenance"])
        self.assertIn("research_algorithm_registry_fingerprint", trace_payload["provenance"])
        self.assertTrue(trace_payload["limitations"])
        self.assertTrue(trace_payload["paper_sources"])
        self.assertTrue(payload["questions"][0]["paper_sources"])
        frontier_paper_hits = [
            row for row in trace_payload["paper_sources"]
            if row["source_type"] == "frontier_stat_paper"
        ]
        self.assertTrue(frontier_paper_hits)
        for row in frontier_paper_hits:
            self.assertIn("expected_theoretical_results", row["withheld_fields"])
            self.assertIn("evaluation_prompt", row["withheld_fields"])
            self.assertNotIn("expected_theoretical_results", row["summary"])
        knowledge_ids = {row["id"] for row in trace_payload["knowledge"]}
        self.assertIn("aipw_double_robustness", knowledge_ids)
        self.assertTrue(
            knowledge_ids
            & {"local_mathlib_probability", "local_statinference_repo", "empirical_process_lean", "lean_stat_learning_theory"}
        )
        self.assertTrue(knowledge_ids & {"lean_finder", "leandojo_reprover", "loogle", "openprover_pipeline"})
        theory_plan = trace_payload["theory_plan"]
        self.assertEqual(theory_plan["plan_version"], 1)
        self.assertEqual(theory_plan["problem_formalization"]["problem_class"], trace_payload["problem"]["problem_class"])
        self.assertEqual(
            {row["id"] for row in theory_plan["candidate_procedures"]},
            {row["id"] for row in trace_payload["procedures"]},
        )
        self.assertEqual(
            {row["id"] for row in theory_plan["theorem_roadmap"]},
            {row["id"] for row in trace_payload["theorem_goals"]},
        )
        self.assertTrue(theory_plan["informal_derivation_steps"][0]["derivation"])
        self.assertTrue(theory_plan["retrieval_context"]["knowledge_cards"])
        self.assertTrue(theory_plan["retrieval_context"]["paper_sources"])
        self.assertTrue(theory_plan["formal_verification_plan"]["formal_gaps"])
        next_agenda = theory_plan["next_iteration_agenda"]
        self.assertEqual(next_agenda["agenda_version"], 1)
        self.assertTrue(next_agenda["items"])
        self.assertIn("formal_verifier", next_agenda["owner_counts"])
        self.assertTrue(next_agenda["stop_condition"])
        agenda_ids = {row["id"] for row in next_agenda["items"]}
        formal_gap_ids = {
            f"formal_gap:{row['id']}"
            for row in trace_payload["formal_subclaims"]
            if row["status"] == "FORMAL_GAP"
        }
        self.assertTrue(formal_gap_ids)
        self.assertTrue(formal_gap_ids <= agenda_ids)
        self.assertFalse(theory_plan["honesty_boundary"]["full_frontier_theorem_proved"])
        extraction = trace_payload["problem"]["extraction_evidence"]
        for key in ("problem_class", "dgp", "estimand", "assumptions", "asymptotic_regime"):
            self.assertTrue(extraction[key], key)
        metric_keys = set(trace_payload["simulations"][0]["metrics"])
        for diagnostic in trace_payload["problem"]["diagnostics"]:
            aliases = DIAGNOSTIC_METRIC_ALIASES.get(diagnostic, ())
            self.assertTrue(diagnostic in metric_keys or any(alias in metric_keys for alias in aliases), diagnostic)
        stress_tests = trace_payload["problem"]["stress_tests"]
        self.assertTrue(stress_tests)
        for simulation in trace_payload["simulations"]:
            diagnosis = simulation["diagnosis"]
            self.assertEqual(diagnosis["status"], "OK")
            self.assertEqual(diagnosis["escalate_to"], "none")
            self.assertTrue(diagnosis["rationale"])
            self.assertIsInstance(diagnosis["metric_evidence"], dict)
            self.assertEqual(set(simulation["stress_tests"]), set(stress_tests))
            self.assertEqual(set(simulation["stress_test_metrics"]), set(stress_tests))
            for stress_row in simulation["stress_test_metrics"].values():
                for key in ("covered", "stress_flag", "primary_value", "threshold"):
                    self.assertIn(key, stress_row)
                    self.assertIsInstance(stress_row[key], (int, float))
        for simulation in payload["questions"][0]["simulations"]:
            self.assertTrue(simulation["stress_tests"])
            self.assertTrue(simulation["stress_test_metrics"])
            self.assertEqual(simulation["diagnosis"]["status"], "OK")
            self.assertEqual(simulation["diagnosis"]["escalate_to"], "none")
        procedure_run = theory_plan["simulation_plan"]["procedure_runs"][0]
        self.assertEqual(procedure_run["diagnosis"], "OK")
        self.assertEqual(procedure_run["escalate_to"], "none")
        for goal in trace_payload["theorem_goals"]:
            self.assertTrue(goal["required_primitives"])
        causal_goals = {row["id"]: row for row in trace_payload["theorem_goals"]}
        self.assertEqual(
            causal_goals["aipw_double_robustness"]["proof_obligations"],
            ["aipw_score_expectation_decompose"],
        )
        algorithm_spec = trace_payload["procedures"][0]["algorithm_spec"]
        self.assertEqual(algorithm_spec["registry_status"], "vetted")
        self.assertEqual(len(algorithm_spec["implementation_hash"]), 64)
        gap_rows = [row for row in trace_payload["formal_subclaims"] if row["status"] == "FORMAL_GAP"]
        self.assertTrue(gap_rows)
        for row in gap_rows:
            self.assertEqual(row["formalization_status"], "lean_skeleton_with_placeholder_assumptions")
            self.assertIn("FORMAL_GAP", row["lean_statement"])
            self.assertIn("Missing formal primitives", row["lean_statement"])
            self.assertIn("Retrieved local Lean/StatInference candidates", row["lean_statement"])
            self.assertIn("Primitive-level local candidates", row["lean_statement"])
            self.assertTrue(row["formal_source_hits"])
            self.assertTrue(row["formal_source_hits"][0]["name"])
            self.assertTrue(row["primitive_formal_source_hits"])
            for primitive in causal_goals[row["id"].split(":")[-1]]["required_primitives"]:
                self.assertIn(primitive, row["primitive_formal_source_hits"])
                self.assertTrue(row["primitive_formal_source_hits"][primitive])
                self.assertTrue(row["primitive_formal_source_hits"][primitive][0]["name"])
            self.assertTrue(Path(row["artifact_path"]).exists())
        procedure_goal_ids = set(trace_payload["procedures"][0]["theorem_goals"])
        theorem_goal_ids = {row["id"] for row in trace_payload["theorem_goals"]}
        gap_goal_ids = {row["id"].split(":")[-1] for row in gap_rows}
        self.assertEqual(procedure_goal_ids, theorem_goal_ids)
        self.assertTrue(procedure_goal_ids <= gap_goal_ids)
        robust_trace = json.loads(Path("runs/test_research_benchmark/robust_mean_mom.json").read_text())
        proved = {
            row["proof_obligation_id"]: row
            for row in robust_trace["formal_subclaims"]
            if row["status"] == "PROVED"
        }
        self.assertEqual(
            proved["mean2_estimator_chebyshev_indep"]["proof_dependencies"],
            [
                "mean2_estimator_expectation",
                "mean2_estimator_variance_indep",
                "estimator_error_chebyshev",
            ],
        )
        self.assertEqual(
            proved["finite_sample_mean_chebyshev_indep"]["proof_dependencies"],
            [
                "finite_sample_mean_unbiased",
                "finite_sample_mean_variance_indep",
                "estimator_error_chebyshev",
            ],
        )

    def test_paper_source_index_retrieves_frontier_sources_without_gold_leakage(self) -> None:
        records = build_paper_source_index()
        self.assertGreaterEqual(len(records), 60)
        self.assertTrue(any(row.source_type == "frontier_stat_paper" for row in records))
        self.assertTrue(any(row.source_type == "ai_math_paper" for row in records))

        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        _procedures, theorem_goals = TheoryPlanner().plan(problem)
        hits = retrieve_paper_sources(question, problem, theorem_goals, records=records, k=5)
        self.assertTrue(hits)
        self.assertTrue(any(hit.source_type == "frontier_stat_paper" for hit in hits))
        for hit in hits:
            self.assertTrue(hit.matched_terms)
            if hit.source_type == "frontier_stat_paper":
                self.assertIn("expected_theoretical_results", hit.withheld_fields)
                self.assertIn("evaluation_prompt", hit.withheld_fields)
                self.assertNotIn("expected_theoretical_results", hit.summary)

    def test_research_markdown_question_file_runs_through_benchmark(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_paper_abstracts.md"))
            return await run_research_benchmark(
                questions,
                Path("runs/test_research_markdown_benchmark"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )

        payload = asyncio.run(run())
        self.assertEqual(payload["n_questions"], 10)
        self.assertEqual(payload["n_ready_with_gaps"], 10)
        self.assertEqual(
            {row["question"] for row in payload["questions"]},
            {
                "causal_ate_paper",
                "conformal_paper",
                "survival_paper",
                "robust_mean_paper",
                "design_variance_paper",
                "robust_regression_paper",
                "fdr_paper",
                "anytime_paper",
                "high_dimensional_pca_paper",
                "extreme_tail_quantile_paper",
            },
        )
        classes = {row["problem_class"] for row in payload["questions"]}
        self.assertEqual(
            classes,
            {
                "semiparametric_causal_ate",
                "distribution_free_conformal_prediction",
                "right_censored_survival_inference",
                "robust_mean_inference",
                "design_based_variance_inference",
                "heteroskedastic_regression_inference",
                "multiple_testing_fdr",
                "sequential_anytime_inference",
                "high_dimensional_pca_inference",
                "extreme_tail_quantile_inference",
            },
        )
        self.assertTrue(Path("runs/test_research_markdown_benchmark/research_benchmark_manifest.json").exists())

    def test_research_report_summarizes_persisted_traces(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_paper_abstracts.md"))[:2]
            await run_research_benchmark(
                questions,
                Path("runs/test_research_report_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=20,
                seed=20260528,
            )
            return build_research_markdown_report(
                Path("runs/test_research_report_run"),
                Path("runs/test_research_report"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["counts"]["questions"], 2)
        self.assertGreater(payload["counts"]["proved_subclaims"], 0)
        self.assertGreater(payload["counts"]["formal_gaps"], 0)
        self.assertEqual(payload["counts"]["simulations"], 2)
        report = Path("runs/test_research_report/research_report.md")
        manifest = Path("runs/test_research_report/research_report_manifest.json")
        self.assertTrue(report.exists())
        self.assertTrue(manifest.exists())
        text = report.read_text(encoding="utf-8")
        self.assertIn("AI Statistical Theory Lab Research Report", text)
        self.assertIn("Problem Extraction", text)
        self.assertIn("Formal Proof Status", text)
        self.assertIn("Simulation Diagnostics", text)
        self.assertIn("Diagnosis:", text)
        self.assertIn("Next Iteration Agenda", text)
        self.assertIn("Source Grounding", text)
        self.assertIn("FORMAL_GAP", text)

    def test_research_trace_audit_validates_frontier_traces(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))
            await run_research_benchmark(
                questions,
                Path("runs/test_research_trace_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )
            return audit_research_traces(
                Path("runs/test_research_trace_run"),
                Path("runs/test_research_trace_audit"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_ok"], 10)
        self.assertEqual(payload["n_traces"], 10)
        self.assertTrue(Path("runs/test_research_trace_audit/research_trace_audit_manifest.json").exists())

    def test_next_iteration_queue_aggregates_trace_agendas(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))[:2]
            await run_research_benchmark(
                questions,
                Path("runs/test_next_iteration_queue_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )
            return audit_next_iteration_queue(
                Path("runs/test_next_iteration_queue_run"),
                Path("runs/test_next_iteration_queue"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertGreater(payload["n_items"], 0)
        self.assertGreater(payload["n_actionable_items"], 0)
        self.assertIn("formal_verifier", payload["by_owner"])
        self.assertIn("FORMAL_GAP", payload["by_trigger"])
        first = payload["rows"][0]
        self.assertTrue(first["item_id"])
        self.assertTrue(first["owner_agent"])
        self.assertTrue(first["action"])
        self.assertTrue(Path("runs/test_next_iteration_queue/next_iteration_queue_manifest.json").exists())
        self.assertTrue(Path("runs/test_next_iteration_queue/next_iteration_queue.md").exists())

    def test_research_gap_backlog_audits_formal_gaps(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))
            await run_research_benchmark(
                questions,
                Path("runs/test_research_gap_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )
            return audit_research_gap_backlog(
                Path("runs/test_research_gap_run"),
                Path("runs/test_research_gap_backlog"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_gaps"], 20)
        self.assertEqual(payload["n_ok"], 20)
        self.assertEqual(payload["n_artifacts_present"], 20)
        self.assertEqual(payload["by_problem_class"]["semiparametric_causal_ate"], 3)
        self.assertTrue(payload["by_required_primitive"])
        first = payload["rows"][0]
        self.assertTrue(first["proved_subclaims"])
        self.assertTrue(first["related_knowledge"])
        self.assertTrue(first["required_primitives"])
        self.assertTrue(first["retrieved_formal_sources"])
        self.assertTrue(Path("runs/test_research_gap_backlog/research_gap_backlog_manifest.json").exists())
        self.assertTrue(Path("runs/test_research_gap_backlog/research_gap_backlog.md").exists())

    def test_formalization_target_audit_prioritizes_gap_primitives(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))
            await run_research_benchmark(
                questions,
                Path("runs/test_formalization_target_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )
            return audit_formalization_targets(
                Path("runs/test_formalization_target_run"),
                Path("runs/test_formalization_target_audit"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertGreater(payload["n_targets"], 0)
        first = payload["rows"][0]
        self.assertTrue(first["primitive"])
        self.assertGreater(first["priority_score"], 0)
        self.assertTrue(first["candidate_declarations"])
        self.assertTrue(first["proof_bank_bridge_available"])
        self.assertTrue(first["bridge_candidate_obligations"])
        self.assertGreater(first["bridge_candidate_score"], 0)
        self.assertIn(first["priority_band"], {"BRIDGE_REUSE_READY", "HIGH_REUSE_BRIDGE_READY"})
        self.assertIn(first["bridge_candidate_obligations"][0], first["suggested_next_step"])
        self.assertIn(first["bridge_readiness"], payload["by_bridge_readiness"])
        self.assertTrue(first["theorem_goals"])
        self.assertTrue(first["suggested_next_step"])
        self.assertGreater(payload["n_with_proof_bank_bridge"], 0)
        self.assertGreater(payload["n_with_ranked_bridge_candidate"], 0)
        self.assertTrue(Path("runs/test_formalization_target_audit/formalization_target_manifest.json").exists())
        self.assertTrue(Path("runs/test_formalization_target_audit/formalization_targets.md").exists())

    def test_formal_gap_task_export_writes_lean_task_jsonl(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))[:2]
            await run_research_benchmark(
                questions,
                Path("runs/test_formal_gap_task_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )
            return export_formal_gap_lean_tasks(
                Path("runs/test_formal_gap_task_run"),
                Path("runs/test_formal_gap_lean_tasks"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertGreater(payload["n_tasks"], 0)
        self.assertEqual(payload["n_ok"], payload["n_tasks"])
        first = payload["tasks"][0]
        self.assertTrue(first["task_id"].startswith("formal_gap:"))
        self.assertIn("Mathlib", first["imports"])
        self.assertEqual(first["namespace"], "AIStatisticianResearchGaps")
        self.assertTrue(first["allowed_sorry"])
        self.assertIn("FORMAL_GAP", first["expected_patterns"])
        self.assertIn("FORMAL_GAP", first["statement"])
        self.assertTrue(first["required_primitives"])
        self.assertTrue(first["retrieved_formal_sources"])
        jsonl = Path(payload["jsonl_path"])
        self.assertTrue(jsonl.exists())
        rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), payload["n_tasks"])
        self.assertTrue(Path("runs/test_formal_gap_lean_tasks/formal_gap_lean_task_manifest.json").exists())
        self.assertTrue(Path("runs/test_formal_gap_lean_tasks/formal_gap_lean_tasks.md").exists())

    def test_research_capability_audit_maps_goal_to_evidence_and_gaps(self) -> None:
        report = build_research_capability_audit(
            root=Path("."),
            question_file=Path("examples/research_questions.json"),
            frontier_benchmark_file=Path("docs/frontier_stat_theory_benchmark.md"),
            max_manifests=4,
        )
        self.assertTrue(report["all_current_release_requirements_met"])
        self.assertFalse(report["goal_complete"])
        self.assertGreaterEqual(report["n_achieved"], 8)
        self.assertGreaterEqual(report["n_partial"], 2)
        self.assertGreaterEqual(report["n_not_achieved"], 1)

        findings = {row["requirement"]: row for row in report["findings"]}
        full_proof = findings["prove full frontier asymptotic/statistical theorem goals in Lean"]
        self.assertEqual(full_proof["status"], "PARTIAL")
        self.assertFalse(full_proof["current_release_gate"])
        available_proofs = findings["prove available Mathlib-backed subclaims in Lean via AXLE"]
        self.assertIn(available_proofs["status"], {"PARTIAL", "ACHIEVED"})
        self.assertTrue(available_proofs["current_release_gate"])
        self.assertTrue(
            any("latest_proof_audit_kernel_verified=" in item for item in available_proofs["evidence"])
        )
        self.assertTrue(
            any("latest_proof_audit_full_bank_kernel_verified=" in item for item in available_proofs["evidence"])
        )
        simulation_diagnosis = findings["classify simulation outcomes and route feedback to the right agent"]
        self.assertEqual(simulation_diagnosis["status"], "ACHIEVED")
        self.assertTrue(simulation_diagnosis["current_release_gate"])
        self.assertTrue(any("SimulationDiagnosis" in item for item in simulation_diagnosis["evidence"]))
        next_iteration = findings[
            "turn proof gaps and simulation diagnoses into a next-iteration research agenda"
        ]
        self.assertEqual(next_iteration["status"], "ACHIEVED")
        self.assertTrue(next_iteration["current_release_gate"])
        self.assertTrue(any("next_iteration_agenda" in item for item in next_iteration["evidence"]))
        arbitrary_frontier = findings[
            "autonomously solve arbitrary frontier journal statistical theory problems end to end"
        ]
        self.assertEqual(arbitrary_frontier["status"], "NOT_ACHIEVED")
        self.assertFalse(arbitrary_frontier["current_release_gate"])
        self.assertGreater(report["frontier_summary"]["n_supported"], 0)
        self.assertGreater(report["frontier_summary"]["n_unsupported"], 0)

        manifest = write_research_capability_audit(report, Path("runs/test_research_capability_audit"))
        self.assertTrue(manifest.exists())
        self.assertTrue(Path("runs/test_research_capability_audit/research_capability_audit.md").exists())
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertFalse(payload["goal_complete"])
        self.assertTrue(payload["all_current_release_requirements_met"])

    def test_prover_component_audit_is_honest_about_training_gaps(self) -> None:
        payload = build_prover_component_audit(root=Path("."))
        self.assertTrue(payload["paper_outline_exists"])
        self.assertFalse(payload["summary"]["honest_goal_complete"])
        statuses = {row["component"]: row["status"] for row in payload["rows"]}
        self.assertEqual(statuses["hard verifier / Lean kernel interface"], "READY")
        self.assertIn("PARTIAL", statuses["premise retrieval / Lean RAG / formal-source search"])
        self.assertEqual(statuses["tactic / whole-proof policy model"], "BASELINE_ONLY")
        self.assertEqual(statuses["model training pipeline"], "MISSING")
        manifest, report = write_prover_component_audit(payload, Path("runs/test_prover_component_audit"))
        self.assertTrue(manifest.exists())
        self.assertTrue(report.exists())

    def test_research_seed_eval_writes_aggregate_manifest(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))
            return await run_research_seed_eval(
                questions,
                ResearchEvalConfig(seeds=(101, 102), n_runs=25),
                Path("runs/test_research_eval"),
                proof_verifier=MockProofVerifier(),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ready_with_gaps"])
        self.assertTrue(payload["all_trace_audits_ok"])
        self.assertEqual(payload["config"]["seeds"], [101, 102])
        self.assertEqual(payload["config"]["verifier"], "mock")
        self.assertEqual(payload["summary"]["causal_ate_aipw"]["trials"], 2)
        self.assertIn("oracle_aipw_ate", payload["summary"]["causal_ate_aipw"]["procedures"])
        self.assertTrue(Path("runs/test_research_eval/research_evaluation_manifest.json").exists())
        self.assertTrue(Path(payload["artifacts"][0]["benchmark_manifest"]).exists())
        self.assertTrue(Path(payload["artifacts"][0]["trace_audit_manifest"]).exists())

    def test_research_system_audit_runs_frontier_gates(self) -> None:
        async def run():
            return await run_research_system_audit(
                Path("runs/test_research_system_audit"),
                question_file=Path("examples/research_questions.json"),
                config=ResearchSystemAuditConfig(n_runs=25, seed=20260528),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_gates_passed"])
        self.assertTrue(payload["gates"]["frontier_coverage_audit"])
        self.assertTrue(payload["gates"]["frontier_precision_audit"])
        self.assertTrue(payload["gates"]["frontier_backlog_audit"])
        self.assertTrue(payload["gates"]["research_capability_audit"])
        self.assertTrue(payload["gates"]["frontier_smoke_benchmark"])
        self.assertTrue(payload["gates"]["research_intake_audit"])
        self.assertTrue(payload["gates"]["research_knowledge_audit"])
        self.assertTrue(payload["gates"]["retrieval_audit"])
        self.assertTrue(payload["gates"]["formal_source_graph"])
        self.assertTrue(payload["gates"]["research_algorithm_audit"])
        self.assertTrue(payload["gates"]["proof_audit"])
        self.assertTrue(payload["gates"]["proof_training_export"])
        self.assertTrue(payload["gates"]["proof_repair_export"])
        self.assertTrue(payload["gates"]["proof_policy_baseline"])
        self.assertTrue(payload["gates"]["prover_component_audit"])
        self.assertTrue(payload["gates"]["research_benchmark"])
        self.assertTrue(payload["gates"]["formal_gap_skeletons"])
        self.assertTrue(payload["gates"]["research_trace_audit"])
        self.assertTrue(payload["gates"]["research_gap_backlog"])
        self.assertTrue(payload["gates"]["formalization_target_audit"])
        self.assertTrue(payload["gates"]["formal_gap_task_export"])
        self.assertTrue(payload["gates"]["next_iteration_queue"])
        self.assertTrue(payload["gates"]["research_report"])
        self.assertEqual(payload["counts"]["questions"], 10)
        self.assertEqual(payload["counts"]["frontier_questions"], 60)
        self.assertGreater(payload["counts"]["frontier_supported"], 0)
        self.assertGreater(payload["counts"]["frontier_unsupported"], 0)
        self.assertEqual(payload["counts"]["frontier_precision_ok"], payload["counts"]["frontier_precision_supported"])
        self.assertEqual(payload["counts"]["frontier_precision_flagged"], 0)
        self.assertEqual(payload["counts"]["frontier_backlog_ok"], payload["counts"]["frontier_backlog_total"])
        self.assertEqual(payload["counts"]["frontier_backlog_total"], payload["counts"]["frontier_unsupported"])
        self.assertGreater(payload["counts"]["frontier_backlog_domains"], 0)
        self.assertGreater(payload["counts"]["frontier_backlog_required_primitives"], 0)
        self.assertFalse(payload["counts"]["research_capability_goal_complete"])
        self.assertEqual(
            payload["counts"]["research_capability_current_release_gate_met"],
            payload["counts"]["research_capability_current_release_gate"],
        )
        self.assertGreaterEqual(payload["counts"]["research_capability_partial"], 2)
        self.assertGreaterEqual(payload["counts"]["research_capability_not_achieved"], 1)
        self.assertGreaterEqual(payload["counts"]["frontier_smoke_questions"], 3)
        self.assertEqual(payload["counts"]["frontier_smoke_ready"], payload["counts"]["frontier_smoke_questions"])
        self.assertEqual(
            payload["counts"]["frontier_theory_targets_scored"],
            payload["counts"]["frontier_theory_targets_total"],
        )
        self.assertEqual(
            payload["counts"]["frontier_theory_targets_total"],
            payload["counts"]["frontier_smoke_questions"],
        )
        self.assertGreater(payload["counts"]["frontier_theory_expected_results"], 0)
        self.assertEqual(payload["counts"]["research_intake_supported_accepted"], payload["counts"]["research_intake_supported"])
        self.assertEqual(payload["counts"]["research_intake_unsupported_rejected"], payload["counts"]["research_intake_unsupported"])
        self.assertEqual(payload["counts"]["research_knowledge_problem_ok"], payload["counts"]["research_knowledge_problem_rows"])
        self.assertEqual(payload["counts"]["research_knowledge_sources_ok"], payload["counts"]["research_knowledge_cards"])
        self.assertEqual(
            payload["counts"]["research_source_inventory_ok"],
            payload["counts"]["research_source_inventory_total"],
        )
        self.assertEqual(
            payload["counts"]["formal_source_graph_queries_ok"],
            payload["counts"]["formal_source_graph_queries"],
        )
        self.assertGreater(payload["counts"]["formal_source_graph_symbols"], 0)
        self.assertGreater(payload["counts"]["formal_source_graph_edges"], 0)
        self.assertEqual(payload["counts"]["research_algorithms_ok"], payload["counts"]["research_algorithms_total"])
        self.assertGreater(payload["counts"]["verifier_cache_hits"], 0)
        self.assertGreater(payload["counts"]["verifier_cache_misses"], 0)
        self.assertGreater(payload["counts"]["verifier_cache_size"], 0)
        self.assertEqual(payload["counts"]["proof_training_examples"], payload["counts"]["proofs_verified"])
        self.assertEqual(
            payload["counts"]["proof_training_train"] + payload["counts"]["proof_training_validation"],
            payload["counts"]["proof_training_examples"],
        )
        self.assertTrue(payload["counts"]["proof_negative_controls_enabled"])
        self.assertEqual(payload["counts"]["proof_attempt_negatives"], payload["counts"]["proofs_total"])
        self.assertEqual(payload["counts"]["proof_repair_examples"], payload["counts"]["proof_attempt_negatives"])
        self.assertEqual(
            payload["counts"]["proof_repair_train"] + payload["counts"]["proof_repair_validation"],
            payload["counts"]["proof_repair_examples"],
        )
        self.assertEqual(
            payload["counts"]["proof_policy_baseline_validation"],
            payload["counts"]["proof_training_validation"],
        )
        self.assertGreater(payload["counts"]["prover_components_total"], 0)
        self.assertFalse(payload["counts"]["prover_component_goal_complete"])
        self.assertGreater(payload["counts"]["prover_components_ready"], 0)
        self.assertGreater(payload["counts"]["prover_components_partial"], 0)
        self.assertGreater(payload["counts"]["prover_components_missing_or_not_trained"], 0)
        self.assertEqual(payload["counts"]["research_traces_ok"], 10)
        self.assertEqual(payload["counts"]["formalized_gaps"], payload["counts"]["formal_gaps"])
        self.assertEqual(payload["counts"]["gap_backlog_ok"], payload["counts"]["gap_backlog_total"])
        self.assertGreater(payload["counts"]["missing_formal_primitives"], 0)
        self.assertEqual(
            payload["counts"]["formalization_targets_ok"],
            payload["counts"]["formalization_targets_total"],
        )
        self.assertGreater(payload["counts"]["formalization_targets_with_proof_bank_bridge"], 0)
        self.assertGreater(payload["counts"]["formalization_targets_total"], 0)
        self.assertEqual(payload["counts"]["formal_gap_lean_tasks_ok"], payload["counts"]["formal_gap_lean_tasks_total"])
        self.assertEqual(payload["counts"]["formal_gap_lean_tasks_total"], payload["counts"]["formal_gaps"])
        self.assertEqual(payload["counts"]["next_iteration_ok"], payload["counts"]["next_iteration_items"])
        self.assertGreater(payload["counts"]["next_iteration_actionable_items"], 0)
        self.assertGreater(payload["counts"]["next_iteration_formal_verifier_items"], 0)
        self.assertEqual(payload["counts"]["research_report_questions"], payload["counts"]["questions"])
        self.assertEqual(payload["counts"]["research_report_formal_gaps"], payload["counts"]["formal_gaps"])
        self.assertEqual(
            payload["counts"]["research_report_simulations_passed"],
            payload["counts"]["research_report_simulations"],
        )
        self.assertTrue(Path("runs/test_research_system_audit/research_system_audit_manifest.json").exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_coverage_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_precision_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_precision_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_backlog_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_backlog_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_capability_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_capability_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_smoke_benchmark"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_target_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_target_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_benchmark"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_intake_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_knowledge_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_source_inventory"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_source_graph"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_source_graph_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_algorithm_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_attempt_log"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_training_export"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_training_train"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_training_validation"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_repair_export"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_repair_train"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_repair_validation"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_policy_baseline"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_policy_baseline_predictions"]).exists())
        self.assertTrue(Path(payload["artifacts"]["prover_component_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["prover_component_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_trace_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_gap_backlog"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formalization_target_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formalization_target_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_gap_lean_tasks"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_gap_lean_tasks_jsonl"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_gap_lean_tasks_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["next_iteration_queue"]).exists())
        self.assertTrue(Path(payload["artifacts"]["next_iteration_queue_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_report_manifest"]).exists())


if __name__ == "__main__":
    unittest.main()
