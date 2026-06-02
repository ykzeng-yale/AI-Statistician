from __future__ import annotations

import asyncio
import json
import shutil
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_statistician.algorithms import audit_algorithm_registry
from ai_statistician.algorithm_repair_promotion import export_algorithm_repair_promotion_queue
from ai_statistician.algorithm_repair_patch_policy_model import (
    load_algorithm_repair_patch_policy_model,
    train_algorithm_repair_patch_policy_model,
)
from ai_statistician.algorithm_repair_production_patch_plan import export_algorithm_repair_production_patch_plan
from ai_statistician.algorithm_repair_reviewed_patch_apply import apply_reviewed_algorithm_repair_source_patches
from ai_statistician.algorithm_repair_reviewed_patch_validate import validate_reviewed_algorithm_repair_patches
from ai_statistician.algorithm_repair_patch_training_export import export_algorithm_repair_patch_training_dataset
from ai_statistician.algorithm_repair_sandbox import evaluate_algorithm_repair_sandbox
from ai_statistician.algorithm_repair_sandbox_apply import apply_algorithm_repair_sandbox_results
from ai_statistician.algorithm_repair_sandbox_patch_eval import evaluate_algorithm_repair_sandbox_patches
from ai_statistician.algorithm_repair_sandbox_rerun import rerun_algorithm_repair_sandbox_applications
from ai_statistician.algorithm_simulation_stress_audit import audit_algorithm_simulation_stress
from ai_statistician.adversarial_intake_audit import audit_adversarial_unsupported_intake
from ai_statistician.architecture_audit import audit_architecture
from ai_statistician.capability_audit import build_capability_audit, write_capability_audit
from ai_statistician.doctor import build_doctor_report, write_doctor_manifest
from ai_statistician.evaluation_benchmark_guidance import build_evaluation_benchmark_guidance
from ai_statistician.frontier_coverage_audit import audit_frontier_coverage, load_frontier_benchmark_questions
from ai_statistician.fresh_holdout_frontier_audit import audit_fresh_holdout_frontier
from ai_statistician.frontier_precision_audit import audit_frontier_precision
from ai_statistician.frontier_smoke_benchmark import FrontierSmokeConfig, run_frontier_smoke_benchmark, select_supported_frontier_questions
from ai_statistician.formal_gap_task_export import export_formal_gap_lean_tasks
from ai_statistician.formalization_target_audit import audit_formalization_targets
from ai_statistician.formal_source_graph import FormalSourceGraphRetriever, audit_formal_source_graph
from ai_statistician.formal_source_hybrid import FormalSourceHybridRetriever
from ai_statistician.formal_source_index import (
    FormalDeclaration,
    FormalSourceHit,
    FormalSourceRoot,
    FormalSourceSqliteIndex,
    audit_formal_source_index,
    build_formal_source_search_backend,
    build_formal_source_index,
    search_formal_sources,
)
from ai_statistician.formal_source_retrieval_benchmark import (
    FormalSourceRetrievalBenchmarkCase,
    run_formal_source_retrieval_benchmark,
)
from ai_statistician.formal_source_retrieval_ablation import run_formal_source_retrieval_ablation_benchmark
from ai_statistician.lean_rag_dependency import LeanRagDependencyRetriever
from ai_statistician.autoform_harness import audit_autoform_harness
from ai_statistician.proof_bank import all_obligations, get_obligation
from ai_statistician.evaluation import EvalConfig, run_seed_eval
from ai_statistician.autoform_target_export import export_autoform_targets
from ai_statistician.intake_audit import audit_question_intake
from ai_statistician.frontier_backlog_audit import audit_frontier_backlog
from ai_statistician.proof_audit import audit_proof_bank
from ai_statistician.proof_bank_expansion_export import export_proof_bank_expansion_candidates
from ai_statistician.primitive_source_coverage_audit import audit_primitive_source_coverage
from ai_statistician.proof_policy_baseline import evaluate_retrieval_proof_policy_baseline
from ai_statistician.proof_policy_model import load_proof_policy_model, train_proof_policy_model
from ai_statistician.proof_repair_export import export_proof_repair_dataset
from ai_statistician.proof_search import BestFirstWholeProofSearchController, ProofCandidate
from ai_statistician.proof_search_audit import audit_proof_search_controller
from ai_statistician.proof_search_retrieval_ablation import run_proof_search_retrieval_ablation
from ai_statistician.proof_search_training_export import export_proof_search_process_dataset
from ai_statistician.proof_search_value_model import (
    load_proof_search_value_model,
    train_proof_search_value_model,
)
from ai_statistician.proof_training_export import export_proof_training_dataset
from ai_statistician.prover_component_audit import build_prover_component_audit, write_prover_component_audit
from ai_statistician.questions import load_question_file, question_from_json
from ai_statistician.release import ReleaseBundleConfig, build_release_bundle
from ai_statistician.research_evaluation import ResearchEvalConfig, run_research_seed_eval
from ai_statistician.research_gap_audit import audit_research_gap_backlog
from ai_statistician.research_intake_audit import audit_research_question_intake
from ai_statistician.research_knowledge_audit import audit_research_knowledge
from ai_statistician.research_source_inventory import (
    ATLAS_LEAN_ROOT,
    BROWNIAN_MOTION_ROOT,
    FORMAL_SLT_ROOT,
    KOLMOGOROV_EXTENSION_ROOT,
    LEAN_MACHINE_LEARNING_ROOT,
    LEAN_RADEMACHER_ROOT,
    SCILEAN_ROOT,
    source_allows_training_export,
)
from ai_statistician.research_capability_audit import (
    build_research_capability_audit,
    write_research_capability_audit,
)
from ai_statistician.research_lab import (
    AIStatisticalTheoryLab,
    attach_research_algorithm_metadata,
    audit_research_algorithm_registry,
    load_open_research_questions,
    ProblemFormalizer,
    ResearchSimulator,
    run_research_benchmark,
    TheoryPlanner,
)
from ai_statistician.research_loop import ResearchLoopCoordinator
from ai_statistician.research_loop_live_repair_audit import audit_research_loop_live_repair_artifacts
from ai_statistician.research_loop_repair_audit import audit_research_loop_repair_tasks
from ai_statistician.research_next_iteration_audit import audit_next_iteration_queue
from ai_statistician.research_paper_index import build_paper_source_index, retrieve_paper_sources
from ai_statistician.research_policy_baseline import evaluate_research_policy_baseline
from ai_statistician.research_report import build_research_markdown_report
from ai_statistician.research_schema import FormalSubclaim, ResearchReport
from ai_statistician.research_system_audit import ResearchSystemAuditConfig, run_research_system_audit
from ai_statistician.research_trace_audit import audit_research_traces
from ai_statistician.research_trace_audit import DIAGNOSTIC_METRIC_ALIASES
from ai_statistician.research_training_export import export_research_training_dataset
from ai_statistician.retrieval import ProofBankRetriever, RetrievalQuery, audit_proof_bank_retrieval
from ai_statistician.schema import FormalObligation, ProofCheck, RetrievalHit
from ai_statistician.system import AIStatisticianSystem
from ai_statistician.system import write_run_manifest, write_trace
from ai_statistician.system_audit import SystemAuditConfig, load_audit_questions, run_system_audit
from ai_statistician.theory_developer import DefaultTheoryDeveloper
from ai_statistician.theory_proposal import MockTheoryProposer, TheoryProposal
from ai_statistician.trace_audit import audit_run_traces
from ai_statistician.verifier import CachingProofVerifier, LocalLeanProofVerifier, MockProofVerifier
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

    def test_retriever_finds_union_budget_control_obligation(self) -> None:
        retriever = ProofBankRetriever()
        hits = retriever.retrieve(
            RetrievalQuery(
                "finite multiple testing familywise error Bonferroni alpha budget",
                tags=("union_bound", "multiple_testing", "familywise_error"),
            ),
            candidates=all_obligations(),
        )
        self.assertTrue(hits)
        self.assertEqual(hits[0].obligation_id, "finite_union_budget_control")

    def test_retriever_finds_difference_variance_obligation(self) -> None:
        retriever = ProofBankRetriever()
        hits = retriever.retrieve(
            RetrievalQuery(
                "difference in means contrast variance covariance decomposition",
                tags=("contrast", "variance", "covariance"),
            ),
            candidates=all_obligations(),
        )
        self.assertTrue(hits)
        self.assertEqual(hits[0].obligation_id, "difference_estimator_variance_decompose")

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
                    "import Mathlib.Probability.Moments.Variance",
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
        self.assertIn("Mathlib", variance_decl.imports)
        self.assertIn("Mathlib.Probability.Moments.Variance", variance_decl.imports)
        shape_hits = search_formal_sources(
            "variance equality with IndepFun premise",
            declarations=declarations,
            k=3,
        )
        self.assertEqual(shape_hits[0].declaration.name, "Demo.variance_sum_indep")
        import_hits = search_formal_sources(
            "Probability Moments Variance import",
            declarations=declarations,
            k=3,
        )
        self.assertEqual(import_hits[0].declaration.name, "Demo.variance_sum_indep")
        sqlite_index = FormalSourceSqliteIndex.build(
            declarations,
            Path("runs/test_formal_source_index/formal_source_index.sqlite"),
        )
        sqlite_hits = sqlite_index.search("variance equality IndepFun premise", k=3)
        self.assertTrue(sqlite_hits)
        self.assertEqual(sqlite_hits[0].declaration.name, "Demo.variance_sum_indep")
        sqlite_declarations = sqlite_index.load_declarations()
        self.assertEqual(len(sqlite_declarations), 2)
        self.assertIn("Mathlib.Probability.Moments.Variance", sqlite_declarations[1].imports)
        graph = FormalSourceGraphRetriever(declarations)
        graph_hits = graph.search("independent variance estimator", k=3)
        self.assertTrue(graph_hits)
        self.assertEqual(graph_hits[0].declaration.name, "Demo.variance_sum_indep")
        self.assertTrue(graph_hits[0].graph_symbols)
        hybrid = FormalSourceHybridRetriever(declarations, sqlite_index)
        hybrid_hits = hybrid.search("independent variance estimator", k=3)
        self.assertTrue(hybrid_hits)
        self.assertEqual(hybrid_hits[0].declaration.name, "Demo.variance_sum_indep")
        self.assertTrue(
            any(term in hybrid_hits[0].matched_terms for term in ("symbol_graph", "sqlite_fts")),
            hybrid_hits[0].matched_terms,
        )
        self.assertEqual(len(hybrid.load_declarations()), 2)
        lean_rag_db = Path("runs/test_lean_rag_dependency/stat_inference.sqlite")
        lean_rag_db.parent.mkdir(parents=True, exist_ok=True)
        if lean_rag_db.exists():
            lean_rag_db.unlink()
        with sqlite3.connect(lean_rag_db) as conn:
            conn.executescript(
                """
                CREATE TABLE declarations (
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL,
                  short_name TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  module TEXT NOT NULL,
                  path TEXT NOT NULL,
                  line_start INTEGER NOT NULL,
                  line_end INTEGER NOT NULL,
                  namespace TEXT NOT NULL,
                  attributes TEXT NOT NULL,
                  signature TEXT NOT NULL,
                  proof TEXT NOT NULL,
                  has_proof INTEGER NOT NULL,
                  has_sorry INTEGER NOT NULL,
                  text_hash TEXT NOT NULL
                );
                CREATE TABLE declaration_edges (
                  id INTEGER PRIMARY KEY,
                  src_decl_id INTEGER NOT NULL,
                  dst_decl_id INTEGER NOT NULL,
                  edge_type TEXT NOT NULL,
                  match_kind TEXT NOT NULL,
                  scope TEXT NOT NULL,
                  weight INTEGER NOT NULL
                );
                CREATE VIRTUAL TABLE decl_fts USING fts5(
                  name, short_name, kind, module, namespace, signature, proof
                );
                """
            )
            rows = [
                (
                    1,
                    "Demo.variance_sum_indep",
                    "variance_sum_indep",
                    "theorem",
                    "Demo",
                    "Demo.lean",
                    5,
                    7,
                    "Demo",
                    "[]",
                    "theorem variance_sum_indep (h : IndepFun X Y mu) : variance (X + Y) mu = variance X mu + variance Y mu",
                    "by trivial",
                    1,
                    0,
                    "hash1",
                ),
                (
                    2,
                    "Demo.consumer_uses_variance_sum_indep",
                    "consumer_uses_variance_sum_indep",
                    "lemma",
                    "Demo",
                    "Demo.lean",
                    9,
                    10,
                    "Demo",
                    "[]",
                    "lemma consumer_uses_variance_sum_indep : True",
                    "by have h := Demo.variance_sum_indep; trivial",
                    1,
                    0,
                    "hash2",
                ),
            ]
            conn.executemany(
                """
                INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.executemany(
                """
                INSERT INTO decl_fts(rowid, name, short_name, kind, module, namespace, signature, proof)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(row[0], row[1], row[2], row[3], row[4], row[8], row[10], row[11]) for row in rows],
            )
            conn.execute(
                """
                INSERT INTO declaration_edges(
                  src_decl_id, dst_decl_id, edge_type, match_kind, scope, weight
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (2, 1, "explicit_source", "qualified", "proof", 1),
            )
        lean_rag = LeanRagDependencyRetriever(lean_rag_db)
        self.assertTrue(lean_rag.is_healthy())
        lean_rag_hits = lean_rag.search("variance independent sum", k=3)
        self.assertTrue(lean_rag_hits)
        self.assertEqual(lean_rag_hits[0].declaration.source_id, "lean_rag_dependency_graph")
        self.assertIn("lean_rag_dependency_graph", lean_rag_hits[0].matched_terms)
        context = lean_rag.dependency_context("Demo.variance_sum_indep")
        self.assertIsNotNone(context)
        assert context is not None
        self.assertEqual(context.fan_in, 1)
        self.assertIn("Demo.consumer_uses_variance_sum_indep", context.used_by)
        hybrid_with_deps = FormalSourceHybridRetriever(
            declarations,
            sqlite_index,
            dependency_retriever=lean_rag,
        )
        fused_hits = hybrid_with_deps.search("variance independent sum", k=5)
        self.assertTrue(
            any("lean_rag_dependency_graph" in hit.matched_terms for hit in fused_hits),
            [(hit.declaration.name, hit.matched_terms) for hit in fused_hits],
        )
        backend_with_deps = build_formal_source_search_backend(
            db_path=Path("runs/test_formal_source_index/with_lean_rag.sqlite"),
            roots=(root,),
            lean_rag_db_path=lean_rag_db,
        )
        self.assertTrue(getattr(backend_with_deps, "lean_rag_dependency_graph_enabled"))
        self.assertEqual(
            Path(getattr(backend_with_deps, "lean_rag_dependency_graph_path")).name,
            "stat_inference.sqlite",
        )
        with patch(
            "ai_statistician.formal_source_index.DEFAULT_LEAN_RAG_DB_CANDIDATES",
            (lean_rag_db,),
        ):
            backend_with_auto_deps = build_formal_source_search_backend(
                db_path=Path("runs/test_formal_source_index/with_auto_lean_rag.sqlite"),
                roots=(root,),
            )
        self.assertTrue(getattr(backend_with_auto_deps, "lean_rag_dependency_graph_enabled"))
        self.assertTrue(getattr(backend_with_auto_deps, "lean_rag_dependency_graph_auto_discovered"))
        self.assertEqual(
            Path(getattr(backend_with_auto_deps, "lean_rag_dependency_graph_path")).name,
            "stat_inference.sqlite",
        )
        with patch(
            "ai_statistician.formal_source_index.DEFAULT_LEAN_RAG_DB_CANDIDATES",
            (lean_rag_db,),
        ):
            memory_backend_with_auto_deps = build_formal_source_search_backend(
                roots=(root,),
            )
        self.assertTrue(getattr(memory_backend_with_auto_deps, "lean_rag_dependency_graph_enabled"))
        self.assertTrue(getattr(memory_backend_with_auto_deps, "lean_rag_dependency_graph_auto_discovered"))
        self.assertEqual(
            Path(getattr(memory_backend_with_auto_deps, "lean_rag_dependency_graph_path")).name,
            "stat_inference.sqlite",
        )
        memory_fused_hits = memory_backend_with_auto_deps.search("variance independent sum", k=5)
        self.assertTrue(
            any("lean_rag_dependency_graph" in hit.matched_terms for hit in memory_fused_hits),
            [(hit.declaration.name, hit.matched_terms) for hit in memory_fused_hits],
        )
        graph_payload = audit_formal_source_graph(
            Path("runs/test_formal_source_graph"),
            declarations=declarations,
            queries=(("variance_graph", "independent variance estimator"),),
        )
        self.assertTrue(graph_payload["all_queries_ok"])
        self.assertEqual(graph_payload["cache"]["status"], "disabled")
        self.assertGreater(graph_payload["n_symbol_nodes"], 0)
        self.assertTrue(Path("runs/test_formal_source_graph/formal_source_graph_manifest.json").exists())
        graph_cache_dir = Path("runs/test_formal_source_graph_cache")
        shutil.rmtree(graph_cache_dir, ignore_errors=True)
        graph_cached_1 = audit_formal_source_graph(
            Path("runs/test_formal_source_graph_cache_miss"),
            declarations=declarations,
            queries=(("variance_graph", "independent variance estimator"),),
            cache_path=graph_cache_dir,
        )
        graph_cached_2 = audit_formal_source_graph(
            Path("runs/test_formal_source_graph_cache_hit"),
            declarations=declarations,
            queries=(("variance_graph", "independent variance estimator"),),
            cache_path=graph_cache_dir,
        )
        self.assertEqual(graph_cached_1["cache"]["status"], "miss")
        self.assertTrue(graph_cached_1["cache"]["stored"])
        self.assertEqual(graph_cached_2["cache"]["status"], "hit")
        self.assertFalse(graph_cached_2["cache"]["stored"])
        self.assertTrue(Path("runs/test_formal_source_graph_cache_hit/formal_source_graph_manifest.json").exists())
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

    def test_formal_source_retrieval_benchmark_measures_gold_family_recall(self) -> None:
        fixture = Path("runs/test_formal_source_retrieval_benchmark_fixture")
        fixture.mkdir(parents=True, exist_ok=True)
        (fixture / "Demo.lean").write_text(
            "\n".join(
                [
                    "import Mathlib",
                    "namespace Demo",
                    "theorem variance_sum_indep",
                    "    (h_indep : IndepFun X Y μ) :",
                    "    variance (X + Y) μ = variance X μ + variance Y μ := by trivial",
                    "theorem unrelated_bound : True := by trivial",
                    "end Demo",
                ]
            ),
            encoding="utf-8",
        )
        declarations = build_formal_source_index(roots=(FormalSourceRoot("fixture", str(fixture)),))
        sqlite_index = FormalSourceSqliteIndex.build(
            declarations,
            Path("runs/test_formal_source_retrieval_benchmark/formal_source_index.sqlite"),
        )
        hybrid = FormalSourceHybridRetriever(declarations, sqlite_index)
        payload = run_formal_source_retrieval_benchmark(
            Path("runs/test_formal_source_retrieval_benchmark"),
            retriever=hybrid,
            cases=(
                FormalSourceRetrievalBenchmarkCase(
                    query_id="fixture_variance",
                    query="independent variance estimator sum",
                    expected_name_fragments=("variance_sum_indep",),
                    expected_source_ids=("fixture",),
                ),
            ),
            k=3,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_ok"], 1)
        self.assertEqual(payload["recall_at_k"], 1.0)
        self.assertEqual(payload["rows"][0]["hit_rank"], 1)
        self.assertTrue(
            Path(
                "runs/test_formal_source_retrieval_benchmark/"
                "formal_source_retrieval_benchmark_manifest.json"
            ).exists()
        )

    def test_formal_source_retrieval_ablation_measures_lean_rag_new_hit(self) -> None:
        fixture = Path("runs/test_formal_source_retrieval_ablation_fixture")
        shutil.rmtree(fixture, ignore_errors=True)
        fixture.mkdir(parents=True, exist_ok=True)
        (fixture / "Demo.lean").write_text(
            "\n".join(
                [
                    "import Mathlib",
                    "namespace Demo",
                    "theorem unrelated_local_source : True := by trivial",
                    "end Demo",
                ]
            ),
            encoding="utf-8",
        )
        declarations = build_formal_source_index(roots=(FormalSourceRoot("fixture_ablation", str(fixture)),))
        sqlite_index = FormalSourceSqliteIndex.build(
            declarations,
            Path("runs/test_formal_source_retrieval_ablation/local.sqlite"),
        )
        lean_rag_db = Path("runs/test_formal_source_retrieval_ablation/stat_inference.sqlite")
        lean_rag_db.parent.mkdir(parents=True, exist_ok=True)
        if lean_rag_db.exists():
            lean_rag_db.unlink()
        with sqlite3.connect(lean_rag_db) as conn:
            conn.executescript(
                """
                CREATE TABLE declarations (
                  id INTEGER PRIMARY KEY,
                  name TEXT NOT NULL,
                  short_name TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  module TEXT NOT NULL,
                  path TEXT NOT NULL,
                  line_start INTEGER NOT NULL,
                  line_end INTEGER NOT NULL,
                  namespace TEXT NOT NULL,
                  attributes TEXT NOT NULL,
                  signature TEXT NOT NULL,
                  proof TEXT NOT NULL,
                  has_proof INTEGER NOT NULL,
                  has_sorry INTEGER NOT NULL,
                  text_hash TEXT NOT NULL
                );
                CREATE TABLE declaration_edges (
                  id INTEGER PRIMARY KEY,
                  src_decl_id INTEGER NOT NULL,
                  dst_decl_id INTEGER NOT NULL,
                  edge_type TEXT NOT NULL,
                  match_kind TEXT NOT NULL,
                  scope TEXT NOT NULL,
                  weight INTEGER NOT NULL
                );
                CREATE VIRTUAL TABLE decl_fts USING fts5(
                  name, short_name, kind, module, namespace, signature, proof
                );
                """
            )
            rows = (
                (
                    1,
                    "Demo.lean_rag_only_variance_bridge",
                    "lean_rag_only_variance_bridge",
                    "theorem",
                    "Demo",
                    "Demo.lean",
                    11,
                    12,
                    "Demo",
                    "[]",
                    "theorem lean_rag_only_variance_bridge : variance finite independent sum bridge",
                    "by trivial",
                    1,
                    0,
                    "hash",
                ),
                (
                    2,
                    "StatInference.vdVWOrderDualFiniteHorizon_mul_integral_upcrossingsBefore_le_integral_pos_part",
                    "vdVWOrderDualFiniteHorizon_mul_integral_upcrossingsBefore_le_integral_pos_part",
                    "theorem",
                    "StatInference.EmpiricalProcess.Theorem243",
                    "StatInference/EmpiricalProcess/Theorem243.lean",
                    6891,
                    6900,
                    "StatInference",
                    "[]",
                    (
                        "theorem vdVWOrderDualFiniteHorizon_mul_integral_upcrossingsBefore_le_integral_pos_part "
                        ": order dual submartingale finite horizon reverse comparison downcrossings"
                    ),
                    "by trivial",
                    1,
                    0,
                    "hash2",
                ),
            )
            for row in rows:
                conn.execute("INSERT INTO declarations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
                conn.execute(
                    """
                    INSERT INTO decl_fts(rowid, name, short_name, kind, module, namespace, signature, proof)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (row[0], row[1], row[2], row[3], row[4], row[8], row[10], row[11]),
                )
        baseline = FormalSourceHybridRetriever(declarations, sqlite_index)
        enhanced = FormalSourceHybridRetriever(
            declarations,
            sqlite_index,
            dependency_retriever=LeanRagDependencyRetriever(lean_rag_db),
        )
        payload = run_formal_source_retrieval_ablation_benchmark(
            Path("runs/test_formal_source_retrieval_ablation"),
            baseline_retriever=baseline,
            enhanced_retriever=enhanced,
            cases=(
                FormalSourceRetrievalBenchmarkCase(
                    query_id="lean_rag_only_bridge",
                    query="variance finite independent sum bridge",
                    expected_name_fragments=("lean_rag_only_variance_bridge",),
                    expected_source_ids=("lean_rag_dependency_graph",),
                ),
            ),
            k=5,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_new_hits"], 2)
        self.assertEqual(payload["n_lost_hits"], 0)
        self.assertEqual(payload["n_dependency_sensitive_cases"], 1)
        self.assertEqual(payload["n_dependency_sensitive_new_hits"], 1)
        self.assertIn(
            "lean_rag_vdvw_order_dual_submartingale",
            payload["dependency_sensitive_query_ids"],
        )
        self.assertEqual(payload["rows"][0]["baseline_hit_rank"], None)
        self.assertEqual(payload["rows"][0]["enhanced_hit_rank"], 1)
        self.assertTrue(
            Path(
                "runs/test_formal_source_retrieval_ablation/"
                "formal_source_retrieval_ablation_manifest.json"
            ).exists()
        )

    def test_formal_source_search_backend_reuses_sqlite_cache(self) -> None:
        fixture = Path("runs/test_formal_source_cache_fixture")
        shutil.rmtree(fixture, ignore_errors=True)
        shutil.rmtree(Path("runs/test_formal_source_cache"), ignore_errors=True)
        fixture.mkdir(parents=True, exist_ok=True)
        (fixture / "CacheDemo.lean").write_text(
            "\n".join(
                [
                    "import Mathlib",
                    "namespace CacheDemo",
                    "lemma cached_variance_lookup : True := by trivial",
                    "end CacheDemo",
                ]
            ),
            encoding="utf-8",
        )
        root = FormalSourceRoot("cache_fixture", str(fixture))
        cache_path = Path("runs/test_formal_source_cache/formal_source_index_cache.sqlite")
        first = build_formal_source_search_backend(
            db_path=Path("runs/test_formal_source_cache/first.sqlite"),
            roots=(root,),
            cache_path=cache_path,
        )
        self.assertEqual(getattr(first, "cache_status"), "miss")
        self.assertTrue(cache_path.exists())
        first_hits = first.search("cached variance lookup", k=3)
        self.assertTrue(first_hits)
        self.assertEqual(first_hits[0].declaration.name, "CacheDemo.cached_variance_lookup")

        second = build_formal_source_search_backend(
            db_path=Path("runs/test_formal_source_cache/second.sqlite"),
            roots=(root,),
            cache_path=cache_path,
        )
        self.assertEqual(getattr(second, "cache_status"), "hit")
        second_hits = second.search("cached variance lookup", k=3)
        self.assertTrue(second_hits)
        self.assertEqual(second_hits[0].declaration.name, "CacheDemo.cached_variance_lookup")

        with sqlite3.connect(cache_path) as conn:
            conn.execute("DROP TABLE declarations_fts")
            conn.commit()

        rebuilt = build_formal_source_search_backend(
            db_path=Path("runs/test_formal_source_cache/rebuilt.sqlite"),
            roots=(root,),
            cache_path=cache_path,
        )
        self.assertEqual(getattr(rebuilt, "cache_status"), "miss")
        rebuilt_hits = rebuilt.search("cached variance lookup", k=3)
        self.assertTrue(rebuilt_hits)
        self.assertEqual(rebuilt_hits[0].declaration.name, "CacheDemo.cached_variance_lookup")

    def test_meta_atlas_sources_are_indexed_for_retrieval_only(self) -> None:
        atlas_probability = ATLAS_LEAN_ROOT / "Atlas" / "TheoryOfProbability"
        atlas_hds = ATLAS_LEAN_ROOT / "Atlas" / "HighDimensionalStatistics"
        atlas_fourier = ATLAS_LEAN_ROOT / "Atlas" / "FourierAnalysis"
        atlas_functional = ATLAS_LEAN_ROOT / "Atlas" / "IntroductionToFunctionalAnalysis"
        atlas_differential = ATLAS_LEAN_ROOT / "Atlas" / "DifferentialAnalysis"
        atlas_projection = ATLAS_LEAN_ROOT / "Atlas" / "ProjectionTheory"
        if not atlas_probability.exists() or not atlas_hds.exists() or not atlas_fourier.exists():
            self.skipTest("atlas-lean checkout is not available")
        roots = (
            FormalSourceRoot("atlas_lean_theory_of_probability", str(atlas_probability)),
            FormalSourceRoot("atlas_lean_high_dimensional_statistics", str(atlas_hds)),
            FormalSourceRoot("atlas_lean_fourier_analysis", str(atlas_fourier)),
            FormalSourceRoot("atlas_lean_functional_analysis", str(atlas_functional)),
            FormalSourceRoot("atlas_lean_differential_analysis", str(atlas_differential)),
            FormalSourceRoot("atlas_lean_projection_theory", str(atlas_projection)),
        )
        declarations = build_formal_source_index(roots=roots)
        source_ids = {decl.source_id for decl in declarations}
        self.assertIn("atlas_lean_theory_of_probability", source_ids)
        self.assertIn("atlas_lean_high_dimensional_statistics", source_ids)
        self.assertIn("atlas_lean_fourier_analysis", source_ids)
        self.assertIn("atlas_lean_functional_analysis", source_ids)
        self.assertIn("atlas_lean_differential_analysis", source_ids)
        self.assertIn("atlas_lean_projection_theory", source_ids)
        hits = search_formal_sources("subGaussian mgf bound high dimensional statistics", declarations=declarations, k=10)
        self.assertTrue(hits)
        self.assertEqual(hits[0].declaration.source_id, "atlas_lean_high_dimensional_statistics")
        probability_hits = search_formal_sources("Borel Cantelli CLT weak convergence probability", declarations=declarations, k=10)
        self.assertTrue(probability_hits)
        self.assertTrue(any(hit.declaration.source_id == "atlas_lean_theory_of_probability" for hit in probability_hits))
        fourier_hits = search_formal_sources(
            "Fourier characteristic function weak convergence finite measures",
            declarations=declarations,
            k=10,
        )
        self.assertTrue(any(hit.declaration.source_id == "atlas_lean_fourier_analysis" for hit in fourier_hits))
        functional_hits = search_formal_sources(
            "Hilbert space orthogonal projection Cauchy Schwarz",
            declarations=declarations,
            k=10,
        )
        self.assertTrue(any(hit.declaration.source_id == "atlas_lean_functional_analysis" for hit in functional_hits))
        projection_hits = search_formal_sources(
            "ProjectionTheory large sieve grid projection geometric incidence",
            declarations=declarations,
            k=10,
        )
        self.assertTrue(any(hit.declaration.source_id == "atlas_lean_projection_theory" for hit in projection_hits))

    def test_external_statistics_analysis_sources_are_indexed_for_reuse(self) -> None:
        roots = (
            FormalSourceRoot("formal_slt", str(FORMAL_SLT_ROOT / "FormalSLT")),
            FormalSourceRoot("lean_rademacher", str(LEAN_RADEMACHER_ROOT / "FoML")),
            FormalSourceRoot(
                "lean_machine_learning_lml",
                str(LEAN_MACHINE_LEARNING_ROOT / "LeanMachineLearning"),
            ),
            FormalSourceRoot("brownian_motion_lean", str(BROWNIAN_MOTION_ROOT / "BrownianMotion")),
            FormalSourceRoot(
                "kolmogorov_extension_lean",
                str(KOLMOGOROV_EXTENSION_ROOT / "KolmogorovExtension4"),
            ),
            FormalSourceRoot("scilean_calculus", str(SCILEAN_ROOT / "SciLean")),
        )
        if not all(Path(root.location).exists() for root in roots):
            self.skipTest("external statistics/analysis Lean source checkouts are not available")
        declarations = build_formal_source_index(roots=roots, max_files_per_root=800)
        source_ids = {decl.source_id for decl in declarations}
        for expected in (
            "formal_slt",
            "lean_rademacher",
            "lean_machine_learning_lml",
            "brownian_motion_lean",
            "kolmogorov_extension_lean",
            "scilean_calculus",
        ):
            self.assertIn(expected, source_ids)

        retrieval_cases = (
            ("formal_slt", "Rademacher PAC VC Azuma stability ERM generalization"),
            ("lean_rademacher", "Rademacher complexity McDiarmid Dudley entropy integral"),
            ("lean_machine_learning_lml", "stochastic bandit regret UCB algorithm"),
            ("brownian_motion_lean", "Brownian Gaussian Kolmogorov Chentsov stochastic process"),
            ("kolmogorov_extension_lean", "Kolmogorov extension projective measure family"),
            ("scilean_calculus", "SciLean derivative gradient jacobian optimization Gaussian"),
        )
        for source_id, query in retrieval_cases:
            hits = search_formal_sources(query, declarations=declarations, k=10)
            self.assertTrue(hits, source_id)
            self.assertTrue(
                any(hit.declaration.source_id == source_id for hit in hits),
                f"{source_id} not retrieved for {query!r}; got {[hit.declaration.source_id for hit in hits]}",
            )

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
        policy_model = train_proof_policy_model(
            Path(training["all_jsonl"]),
            Path("runs/test_proof_policy_model"),
            validation_jsonl=Path(training["all_jsonl"]),
            k=2,
            epochs=30,
            negatives_per_query=1,
        )
        self.assertEqual(policy_model["n_train"], 2)
        self.assertEqual(policy_model["n_validation"], 2)
        self.assertEqual(policy_model["n_features"], 11)
        self.assertEqual(policy_model["train_top1_exact"], 2)
        self.assertTrue(Path(policy_model["model_json"]).exists())
        model_payload = json.loads(Path(policy_model["model_json"]).read_text(encoding="utf-8"))
        self.assertEqual(model_payload["model_type"], "logistic_whole_proof_ranker")

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

    def test_best_first_whole_proof_search_logs_failed_probe_then_solves(self) -> None:
        async def run():
            obligation = get_obligation("variance_nonneg")
            controller = BestFirstWholeProofSearchController(MockProofVerifier())
            return await controller.solve(
                obligation,
                max_nodes=3,
                retrieval_hits=[
                    RetrievalHit(
                        obligation_id="markov_inequality",
                        score=7.0,
                        source="unit_test_retrieval",
                        matched_terms=("inequality",),
                    )
                ],
                extra_candidates=[
                    ProofCandidate(
                        candidate_id="bad:first",
                        proof_body="by\n  sorry",
                        source="invalid_probe",
                        score=1500.0,
                    )
                ],
            )

        result = asyncio.run(run())
        self.assertTrue(result.solved)
        self.assertEqual(result.nodes_expanded, 2)
        self.assertEqual(result.nodes[0].source, "invalid_probe")
        self.assertFalse(result.nodes[0].ok)
        self.assertEqual(result.selected_source, "registered_proof_body")
        self.assertFalse(result.kernel_verified)
        self.assertEqual(result.schema_version, 6)
        self.assertGreater(result.tactic_template_candidates_total, 0)
        self.assertGreater(result.retrieval_candidates_total, 0)
        self.assertEqual(result.formal_source_candidates_total, 0)

    def test_best_first_whole_proof_search_uses_trained_policy_scores(self) -> None:
        examples = [
            {
                "example_id": "variance_nonneg:train",
                "obligation_id": "variance_nonneg",
                "prompt": "variance nonnegative expected lemma variance_nonneg",
                "completion": "by\n  exact variance_nonneg X μ",
                "expected_lemmas": ["variance_nonneg X μ"],
                "retrieved_obligations": [],
                "tags": ["variance"],
            },
            {
                "example_id": "markov_inequality:train",
                "obligation_id": "markov_inequality",
                "prompt": "markov inequality tail probability integral bound",
                "completion": "by\n  simpa using hf.meas_ge_le_lintegral_div hε hεt",
                "expected_lemmas": ["hf.meas_ge_le_lintegral_div hε hεt"],
                "retrieved_obligations": [],
                "tags": ["probability", "inequality"],
            },
        ]
        train_path = Path("runs/test_policy_guided_search_examples.jsonl")
        train_path.parent.mkdir(parents=True, exist_ok=True)
        train_path.write_text("\n".join(json.dumps(row) for row in examples) + "\n", encoding="utf-8")
        policy_manifest = train_proof_policy_model(
            train_path,
            Path("runs/test_policy_guided_search_model"),
            validation_jsonl=train_path,
            k=2,
            epochs=30,
            negatives_per_query=1,
        )
        policy_model = load_proof_policy_model(Path(str(policy_manifest["model_json"])))

        async def run():
            obligation = get_obligation("variance_nonneg")
            controller = BestFirstWholeProofSearchController(
                MockProofVerifier(),
                proof_policy_model=policy_model,
            )
            return await controller.solve(obligation, max_nodes=2)

        result = asyncio.run(run())
        self.assertTrue(result.solved)
        self.assertIsNotNone(result.nodes[0].policy_score)
        self.assertIsNotNone(result.nodes[0].base_score)
        self.assertGreater(result.nodes[0].score, result.nodes[0].base_score)

    def test_proof_search_audit_exports_node_level_results(self) -> None:
        class DummyFormalSourceRetriever:
            def search(self, query: str, *, k: int = 10):
                return [
                    FormalSourceHit(
                        FormalDeclaration(
                            source_id="unit_formal_source",
                            source_type="lean_library",
                            path="Unit/Formal.lean",
                            line=1,
                            kind="theorem",
                            name="unit_variance_nonneg",
                            namespace="Unit",
                            signature="theorem unit_variance_nonneg : 0 <= variance X μ",
                        ),
                        9.0,
                        ("variance",),
                    )
                ][:k]

        async def run():
            return await audit_proof_search_controller(
                Path("runs/test_proof_search_audit"),
                verifier=MockProofVerifier(),
                max_obligations=2,
                max_nodes=3,
                include_invalid_probe=True,
                formal_source_retriever=DummyFormalSourceRetriever(),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_solved"])
        self.assertEqual(payload["n_obligations"], 2)
        self.assertEqual(payload["nodes_expanded"], 4)
        self.assertGreater(payload["tactic_template_candidates_total"], 0)
        self.assertTrue(payload["formal_source_retriever_enabled"])
        self.assertEqual(payload["formal_source_candidates_total"], 4)
        results_path = Path(payload["results_jsonl"])
        self.assertTrue(results_path.exists())
        rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows[0]["schema_version"], 6)
        self.assertGreater(rows[0]["tactic_template_candidates_total"], 0)
        self.assertGreater(rows[0]["retrieval_candidates_total"], 0)
        self.assertGreater(rows[0]["formal_source_candidates_total"], 0)
        self.assertGreater(payload["retrieval_candidates_total"], 0)
        self.assertEqual(rows[0]["nodes"][0]["source"], "invalid_probe")
        self.assertIn("proof_body", rows[0]["nodes"][0])
        self.assertIn("policy_score", rows[0]["nodes"][0])
        self.assertIn("value_score", rows[0]["nodes"][0])
        self.assertFalse(rows[0]["nodes"][0]["ok"])
        self.assertEqual(rows[0]["selected_source"], "registered_proof_body")
        process = export_proof_search_process_dataset(
            results_path,
            Path("runs/test_proof_search_process_export"),
            validation_fraction=0.0,
        )
        self.assertEqual(process["n_process_examples"], 4)
        self.assertEqual(process["n_positive"], 2)
        self.assertEqual(process["n_negative"], 2)
        self.assertEqual(process["n_train"], 4)
        process_rows = [
            json.loads(line)
            for line in Path(process["all_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(process_rows[0]["task"], "lean_whole_proof_process_reward")
        self.assertEqual(process_rows[0]["reward"], 0.0)
        self.assertIn("Candidate proof body", process_rows[0]["prompt"])
        self.assertIn("candidate still contains sorry", process_rows[0]["first_error"])
        value_model = train_proof_search_value_model(
            Path(process["train_jsonl"]),
            Path("runs/test_proof_search_value_model"),
            validation_jsonl=Path(process["all_jsonl"]),
            epochs=80,
            learning_rate=0.2,
        )
        self.assertEqual(value_model["n_train"], 4)
        self.assertEqual(value_model["n_validation"], 4)
        self.assertEqual(value_model["n_features"], 12)
        self.assertGreaterEqual(value_model["validation_accuracy"], 0.75)
        self.assertTrue(Path(value_model["model_json"]).exists())
        model_payload = json.loads(Path(value_model["model_json"]).read_text(encoding="utf-8"))
        self.assertEqual(model_payload["model_type"], "logistic_feature_baseline")
        loaded_value_model = load_proof_search_value_model(Path(str(value_model["model_json"])))

        async def run_value_guided():
            obligation = get_obligation("variance_nonneg")
            controller = BestFirstWholeProofSearchController(
                MockProofVerifier(),
                proof_value_model=loaded_value_model,
            )
            return await controller.solve(
                obligation,
                max_nodes=2,
                extra_candidates=[
                    ProofCandidate(
                        candidate_id="bad:first",
                        proof_body="by\n  sorry",
                        source="invalid_probe",
                        score=1500.0,
                    )
                ],
            )

        value_guided = asyncio.run(run_value_guided())
        self.assertTrue(value_guided.solved)
        self.assertIsNotNone(value_guided.nodes[0].value_score)
        self.assertEqual(value_guided.nodes[0].source, "registered_proof_body")

    def test_proof_search_retrieval_ablation_tracks_candidate_frontier_delta(self) -> None:
        declaration = FormalDeclaration(
            source_id="enhanced_fixture",
            source_type="lean_library",
            path="Enhanced.lean",
            line=1,
            kind="theorem",
            name="Enhanced.fixture_bridge",
            namespace="Enhanced",
            signature="theorem fixture_bridge : True",
        )

        class EmptyRetriever:
            def search(self, query: str, *, k: int = 10):
                return []

        class EnhancedRetriever:
            def search(self, query: str, *, k: int = 10):
                return [FormalSourceHit(declaration, 25.0, ("enhanced", "bridge"))][:k]

        payload = asyncio.run(
            run_proof_search_retrieval_ablation(
                Path("runs/test_proof_search_retrieval_ablation"),
                baseline_retriever=EmptyRetriever(),
                enhanced_retriever=EnhancedRetriever(),
                verifier=MockProofVerifier(),
                max_obligations=2,
                max_nodes=2,
                formal_source_k=1,
            )
        )
        self.assertTrue(payload["all_ok"])
        self.assertGreater(payload["formal_source_candidate_delta"], 0)
        self.assertEqual(payload["solved_delta"], 0)
        self.assertTrue(payload["no_solved_regression"])
        self.assertTrue(
            Path(
                "runs/test_proof_search_retrieval_ablation/"
                "proof_search_retrieval_ablation_manifest.json"
            ).exists()
        )
        self.assertTrue(
            Path(
                "runs/test_proof_search_retrieval_ablation/proof_search_retrieval_ablation.md"
            ).exists()
        )

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

    def test_caching_verifier_delegates_batch_verification(self) -> None:
        class BatchVerifier:
            name = "batch-test"

            def __init__(self) -> None:
                self.n_batch_calls = 0

            async def verify_many(
                self,
                items: list[tuple[FormalObligation, str, list[RetrievalHit]]],
            ) -> list[ProofCheck]:
                self.n_batch_calls += 1
                return [
                    ProofCheck(
                        obligation_id=obligation.id,
                        ok=True,
                        proof_body=proof_body,
                        verifier=self.name,
                        verification_strength="batch-test",
                        kernel_verified=True,
                        retrieval_hits=retrieval_hits,
                    )
                    for obligation, proof_body, retrieval_hits in items
                ]

            async def verify(
                self,
                obligation: FormalObligation,
                proof_body: str,
                retrieval_hits: list[RetrievalHit],
            ) -> ProofCheck:
                raise AssertionError("verify_many should be used for batch-capable verifiers")

        async def run():
            base = BatchVerifier()
            verifier = CachingProofVerifier(base)
            obligation = get_obligation("prob_measure_univ")
            first = await verifier.verify_many([(obligation, obligation.proof_body, [])])
            second = await verifier.verify_many([(obligation, obligation.proof_body, [])])
            return base, verifier, first, second

        base, verifier, first, second = asyncio.run(run())
        self.assertEqual(base.n_batch_calls, 1)
        self.assertTrue(first[0].kernel_verified)
        self.assertTrue(second[0].kernel_verified)
        self.assertEqual(verifier.cache_info(), {"hits": 1, "misses": 1, "size": 1})

    def test_local_lean_verifier_checks_mathlib_proof_when_available(self) -> None:
        lean_project = Path("/Users/yukang/LeanProjects/LeanPractice")
        if shutil.which("lake") is None or not (lean_project / "lakefile.toml").exists():
            raise unittest.SkipTest("local Lake/Mathlib project not available")

        async def run():
            verifier = LocalLeanProofVerifier(project_root=lean_project, timeout_s=90)
            obligation = get_obligation("prob_measure_univ")
            return await verifier.verify(obligation, obligation.proof_body, [])

        check = asyncio.run(run())
        self.assertTrue(check.ok, check.errors[:1])
        self.assertTrue(check.kernel_verified)
        self.assertEqual(check.verifier, "local.lake_env_lean")
        self.assertEqual(check.verification_strength, "local_lean_kernel")

    def test_local_lean_verifier_rejects_sorry_before_compile(self) -> None:
        async def run():
            verifier = LocalLeanProofVerifier(project_root="/definitely/not/a/lake/project", timeout_s=1)
            obligation = get_obligation("prob_measure_univ")
            return await verifier.verify(obligation, "by\n  sorry", [])

        check = asyncio.run(run())
        self.assertFalse(check.ok)
        self.assertFalse(check.kernel_verified)
        self.assertEqual(check.verification_strength, "local_lean_placeholder_rejected")
        self.assertIn("candidate still contains sorry", check.errors)

    def test_local_lean_proof_audit_batches_mathlib_proofs_when_available(self) -> None:
        lean_project = Path("/Users/yukang/LeanProjects/LeanPractice")
        if shutil.which("lake") is None or not (lean_project / "lakefile.toml").exists():
            raise unittest.SkipTest("local Lake/Mathlib project not available")

        async def run():
            return await audit_proof_bank(
                LocalLeanProofVerifier(project_root=lean_project, timeout_s=90),
                Path("runs/test_local_lean_batch_audit"),
                ids=["prob_measure_univ", "integral_of_constant"],
                export_lean=False,
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_verified"])
        self.assertTrue(payload["all_kernel_verified"])
        self.assertEqual(payload["verification_strength"], "local_lean_kernel_batch")

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
                    "finite_horizon_evalue_markov_type1_control",
                    "filtration_mono_measurable_set",
                    "stopping_time_le_event_measurable",
                    "submartingale_expected_stopped_value_mono",
                    "submartingale_stopped_process",
                    "supermartingale_expected_stopped_value_antimono",
                    "submartingale_doob_maximal_ineq",
                    "submartingale_doob_maximal_budget",
                    "submartingale_doob_maximal_probability_bound",
                    "mean2_estimator_chebyshev_indep",
                    "finite_sample_mean_chebyshev_indep",
                    "finite_family_absolute_error_simultaneous_coverage",
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
        self.assertEqual(
            rows["finite_horizon_evalue_markov_type1_control"]["depends_on"],
            ["markov_inequality", "finite_union_bound", "finite_union_budget_control"],
        )
        self.assertEqual(
            rows["finite_family_absolute_error_simultaneous_coverage"]["depends_on"],
            [
                "finite_family_absolute_error_union_control",
                "simultaneous_coverage_of_union_error_bound",
                "coverage_lower_bound_of_complement_error",
            ],
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

    def test_difference_estimator_unbiased_supports_contrast_estimands(self) -> None:
        obligation = get_obligation("difference_estimator_unbiased")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("def differenceEstimator", content)
        self.assertIn("theorem differenceEstimator_unbiased", content)
        self.assertIn("thetaX - thetaY", content)
        self.assertIn("integral_sub", content)
        self.assertIn("difference_in_means", obligation.tags)
        self.assertIn("causal", obligation.tags)
        self.assertIn("design_based", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_neyman_variance_conservative_algebra_supports_design_based_gap(self) -> None:
        obligation = get_obligation("neyman_variance_conservative_algebra")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("difference_estimator_variance_decompose", "variance_nonneg"),
        )
        self.assertIn("theorem neymanVariance_conservative_of_nonneg_effect_variance", content)
        self.assertIn("exactVariance = observableBound - treatmentEffectVariance", content)
        self.assertIn("exactVariance ≤ observableBound", content)
        self.assertIn("nlinarith", content)
        self.assertIn("design_based", obligation.tags)
        self.assertIn("neyman", obligation.tags)
        self.assertIn("randomization_variance", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_finite_population_ate_mean_difference_formalizes_potential_outcome_target(self) -> None:
        obligation = get_obligation("finite_population_ate_mean_difference")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("difference_estimator_unbiased",))
        self.assertIn("def finitePopulationMean", content)
        self.assertIn("theorem finitePopulationATE_mean_difference", content)
        self.assertIn("finitePopulationMean (fun i => Y1 i - Y0 i)", content)
        self.assertIn("finitePopulationMean Y1 - finitePopulationMean Y0", content)
        self.assertIn("Finset.sum_sub_distrib", content)
        self.assertIn("ring", content)
        self.assertIn("finite_population", obligation.tags)
        self.assertIn("potential_outcomes", obligation.tags)
        self.assertIn("design_based", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_potential_outcome_observed_consistency_uses_if_simp(self) -> None:
        obligation = get_obligation("potential_outcome_observed_consistency")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("finite_population_ate_mean_difference",))
        self.assertIn("def observedPotentialOutcome", content)
        self.assertIn("if W i then Y1 i else Y0 i", content)
        self.assertIn("theorem observedPotentialOutcome_consistency", content)
        self.assertIn("W i = true → observedPotentialOutcome Y1 Y0 W i = Y1 i", content)
        self.assertIn("W i = false → observedPotentialOutcome Y1 Y0 W i = Y0 i", content)
        self.assertIn("simp [observedPotentialOutcome, h]", content)
        self.assertIn("potential_outcome_consistency", obligation.tags)
        self.assertIn("binary_treatment", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_propensity_score_lower_bound_gives_nonzero_denominator(self) -> None:
        obligation = get_obligation("propensity_score_ne_zero_of_lower_bound")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("potential_outcome_observed_consistency",))
        self.assertIn("theorem propensityScore_ne_zero_of_lower_bound", content)
        self.assertIn("(hδ : 0 < δ) (hp : δ ≤ p)", content)
        self.assertIn("p ≠ 0", content)
        self.assertIn("lt_of_lt_of_le hδ hp", content)
        self.assertIn("ne_of_gt hp_pos", content)
        self.assertIn("positivity", obligation.tags)
        self.assertIn("propensity_score", obligation.tags)
        self.assertIn("denominator_safety", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_propensity_weight_cancel_uses_lower_bound_denominator_safety(self) -> None:
        obligation = get_obligation("propensity_weight_mul_cancel_of_lower_bound")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("propensity_score_ne_zero_of_lower_bound",))
        self.assertIn("theorem propensityWeight_mul_cancel_of_lower_bound", content)
        self.assertIn("(hδ : 0 < δ) (hp : δ ≤ p)", content)
        self.assertIn("p⁻¹ * p = 1", content)
        self.assertIn("lt_of_lt_of_le hδ hp", content)
        self.assertIn("inv_mul_cancel₀", content)
        self.assertIn("propensity_weight_identity", obligation.tags)
        self.assertIn("aipw", obligation.tags)
        self.assertIn("denominator_safety", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_propensity_weight_left_cancel_complements_weight_identity_bridge(self) -> None:
        obligation = get_obligation("propensity_weight_cancel_left_of_lower_bound")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("propensity_weight_mul_cancel_of_lower_bound",))
        self.assertIn("theorem propensityWeight_cancel_left_of_lower_bound", content)
        self.assertIn("(hδ : 0 < δ) (hp : δ ≤ p)", content)
        self.assertIn("p * p⁻¹ = 1", content)
        self.assertIn("lt_of_lt_of_le hδ hp", content)
        self.assertIn("mul_inv_cancel₀", content)
        self.assertIn("propensity_weight_identity", obligation.tags)
        self.assertIn("left_cancellation", obligation.tags)
        self.assertIn("aipw", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_complete_randomization_uniform_assignment_mass_uses_mathlib_pmf_uniform(self) -> None:
        obligation = get_obligation("complete_randomization_uniform_assignment_mass")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("finite_population_ate_mean_difference",))
        self.assertIn("theorem completeRandomization_uniform_assignment_mass", content)
        self.assertIn("PMF.uniformOfFintype Assignment a", content)
        self.assertIn("(Fintype.card Assignment : ENNReal)⁻¹", content)
        self.assertIn("PMF.uniformOfFintype_apply", content)
        self.assertIn("complete_randomization_distribution", obligation.tags)
        self.assertIn("design_based", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_uniform_rank_pmf_mass_uses_mathlib_uniform_rank_distribution(self) -> None:
        obligation = get_obligation("uniform_rank_pmf_mass")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("complete_randomization_uniform_assignment_mass",))
        self.assertIn("theorem uniformRank_pmf_mass", content)
        self.assertIn("PMF.uniformOfFintype (Fin n) r", content)
        self.assertIn("(n : ENNReal)⁻¹", content)
        self.assertIn("PMF.uniformOfFintype_apply", content)
        self.assertIn("Fintype.card_fin", content)
        self.assertIn("exchangeable_scores", obligation.tags)
        self.assertIn("rank_uniformity", obligation.tags)
        self.assertIn("conformal", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_aipw_score_expectation_target_cancels_augmentation_means(self) -> None:
        obligation = get_obligation("aipw_score_expectation_target_of_aug_cancel")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("aipw_score_expectation_decompose",))
        self.assertIn("def aipwScore", content)
        self.assertIn("theorem aipwScore_expectation_eq_target_of_aug_cancel", content)
        self.assertIn("hContrastMean", content)
        self.assertIn("hAugCancel", content)
        self.assertIn("∫ ω, aipwScore contrast treatAug controlAug ω ∂μ = psi", content)
        self.assertIn("integral_add", content)
        self.assertIn("integral_sub", content)
        self.assertIn("double_robustness", obligation.tags)
        self.assertIn("conditional_mean_residual_zero", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_conditional_mean_residual_zero_bridge_centers_mean(self) -> None:
        obligation = get_obligation("conditional_mean_residual_zero_of_mean_eq")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem conditionalMeanResidual_zero_of_mean_eq", content)
        self.assertIn("hMean : ∫ ω, Y ω ∂μ = m", content)
        self.assertIn("∫ ω, (Y ω - m) ∂μ = 0", content)
        self.assertIn("integral_sub", content)
        self.assertIn("integrable_const", content)
        self.assertIn("conditional_mean_residual_zero", obligation.tags)
        self.assertIn("exogeneity_moment_condition", obligation.tags)
        self.assertIn("nuisance_correctness_cases", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_condexp_integral_eq_integral_real_wraps_total_expectation(self) -> None:
        obligation = get_obligation("condexp_integral_eq_integral_real")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem condExp_integral_eq_integral_real", content)
        self.assertIn("∫ ω, μ[X | m] ω ∂μ = ∫ ω, X ω ∂μ", content)
        self.assertIn("integral_condExp", content)
        self.assertIn("conditional_expectation", obligation.tags)
        self.assertIn("iterated_expectation", obligation.tags)
        self.assertIn("law_of_total_expectation", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_condexp_tower_of_sub_sigma_real_wraps_tower_property(self) -> None:
        obligation = get_obligation("condexp_tower_of_sub_sigma_real")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("condexp_integral_eq_integral_real",))
        self.assertIn("theorem condExp_tower_of_sub_sigma_real", content)
        self.assertIn("hm12 : m1 ≤ m2", content)
        self.assertIn("μ[μ[X | m2] | m1] =ᵐ[μ] μ[X | m1]", content)
        self.assertIn("condExp_condExp_of_le", content)
        self.assertIn("conditional_expectation", obligation.tags)
        self.assertIn("iterated_expectation", obligation.tags)
        self.assertIn("tower_property", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_integrable_ae_tendsto_condexp_filtration_wraps_upward_theorem(self) -> None:
        obligation = get_obligation("integrable_ae_tendsto_condexp_filtration")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("martingale_ae_eq_condexp_limit_process",))
        self.assertIn("conditional_expectation", obligation.tags)
        self.assertIn("almost_everywhere_convergence", obligation.tags)
        self.assertIn("iterated_expectation", obligation.tags)
        self.assertIn("exogeneity_moment_condition", obligation.tags)
        self.assertIn("theorem integrable_tendsto_ae_condExp_filtration_bridge", content)
        self.assertIn("StronglyMeasurable[⨆ n, 𝒢 n] g", content)
        self.assertIn("∀ᵐ x ∂μ, Tendsto", content)
        self.assertIn("hg.tendsto_ae_condExp hgmeas", content)
        self.assertNotIn("by sorry", content)

    def test_integrable_l1_tendsto_condexp_filtration_wraps_upward_theorem(self) -> None:
        obligation = get_obligation("integrable_l1_tendsto_condexp_filtration")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("integrable_ae_tendsto_condexp_filtration",))
        self.assertIn("conditional_expectation", obligation.tags)
        self.assertIn("l1_convergence", obligation.tags)
        self.assertIn("iterated_expectation", obligation.tags)
        self.assertIn("martingale_definition", obligation.tags)
        self.assertIn("theorem integrable_tendsto_eLpNorm_condExp_filtration_bridge", content)
        self.assertIn("eLpNorm (μ[g | 𝒢 n] - g) 1 μ", content)
        self.assertIn("hg.tendsto_eLpNorm_condExp hgmeas", content)
        self.assertNotIn("by sorry", content)

    def test_conditional_mean_residual_zero_bridge_uses_conditional_expectation(self) -> None:
        obligation = get_obligation("conditional_mean_residual_zero_of_condExp_ae_eq")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("condexp_integral_eq_integral_real", "conditional_mean_residual_zero_of_mean_eq"),
        )
        self.assertIn("theorem conditionalMeanResidual_integral_zero_of_condExp_ae_eq", content)
        self.assertIn("hcond : μ[outcome | scoreSigma] =ᵐ[μ] scoreVersion", content)
        self.assertIn("∫ ω, (outcome ω - scoreVersion ω) ∂μ = 0", content)
        self.assertIn("integral_condExp", content)
        self.assertIn("integral_congr_ae", content)
        self.assertIn("integral_sub", content)
        self.assertIn("conditional_expectation", obligation.tags)
        self.assertIn("conditional_mean_residual_zero", obligation.tags)
        self.assertIn("orthogonal_score", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_aipw_score_expectation_target_of_zero_aug_supports_residual_zero_bridge(self) -> None:
        obligation = get_obligation("aipw_score_expectation_target_of_zero_aug")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "aipw_score_expectation_decompose",
                "aipw_score_expectation_target_of_aug_cancel",
                "conditional_mean_residual_zero_of_condExp_ae_eq",
                "conditional_mean_residual_zero_of_mean_eq",
            ),
        )
        self.assertIn("def aipwScore", content)
        self.assertIn("theorem aipwScore_expectation_eq_target_of_zero_aug", content)
        self.assertIn("hTreatZero", content)
        self.assertIn("hControlZero", content)
        self.assertIn("∫ ω, aipwScore contrast treatAug controlAug ω ∂μ = psi", content)
        self.assertIn("conditional_mean_residual_zero", obligation.tags)
        self.assertIn("zero_residual", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_aipw_score_integrability_follows_from_components(self) -> None:
        obligation = get_obligation("aipw_score_integrable_of_components")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("aipw_score_expectation_decompose",))
        self.assertIn("def aipwScore", content)
        self.assertIn("theorem aipwScore_integrable_of_components", content)
        self.assertIn("Integrable (aipwScore contrast treatAug controlAug) μ", content)
        self.assertIn("(hContrast.add hTreat).sub hControl", content)
        self.assertIn("integrability_of_score_terms", obligation.tags)
        self.assertIn("asymptotic_normality", obligation.tags)
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

    def test_median_of_means_failure_union_control_uses_bad_block_union(self) -> None:
        obligation = get_obligation("median_of_means_failure_union_control")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("block_estimator_chebyshev_bound", "finite_union_budget_control"),
        )
        self.assertIn("theorem medianOfMeans_failure_union_control", content)
        self.assertIn("MedianBad ⊆ ⋃ i ∈ Blocks, BadBlock i", content)
        self.assertIn("μ MedianBad ≤ α_total", content)
        self.assertIn("measure_mono", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("Finset.sum_le_sum", content)
        self.assertIn("block_mean_definition", obligation.tags)
        self.assertIn("independent_blocks", obligation.tags)
        self.assertIn("median_of_means_deviation", obligation.tags)
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

    def test_finite_horizon_evalue_markov_bridge_supports_eprocess_gap(self) -> None:
        obligation = get_obligation("finite_horizon_evalue_markov_type1_control")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("markov_inequality", "finite_union_bound", "finite_union_budget_control"),
        )
        self.assertIn("eprocess_type1_control", obligation.tags)
        self.assertIn("nonnegative_supermartingale", obligation.tags)
        self.assertIn("ville_inequality", obligation.tags)
        self.assertIn("theorem finiteHorizonEValue_markov_type1_control", content)
        self.assertIn("μ (⋃ i ∈ I, {ω | u i ≤ E i ω}) ≤ α_total", content)
        self.assertIn("meas_ge_le_lintegral_div", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("Finset.sum_le_sum", content)
        self.assertNotIn("by sorry", content)

    def test_filtration_mono_bridge_supports_sequential_gap(self) -> None:
        obligation = get_obligation("filtration_mono_measurable_set")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("filtration", obligation.tags)
        self.assertIn("sequential", obligation.tags)
        self.assertIn("optional_stopping", obligation.tags)
        self.assertIn("theorem filtration_mono_measurableSet", content)
        self.assertIn("MeasurableSet[ℱ i] A", content)
        self.assertIn("MeasurableSet[ℱ j] A", content)
        self.assertIn("ℱ.mono hij", content)
        self.assertNotIn("by sorry", content)

    def test_stopping_time_le_event_bridge_supports_sequential_gap(self) -> None:
        obligation = get_obligation("stopping_time_le_event_measurable")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("stopping_time", obligation.tags)
        self.assertIn("sequential", obligation.tags)
        self.assertIn("optional_stopping", obligation.tags)
        self.assertIn("theorem stoppingTime_le_event_measurable", content)
        self.assertIn("IsStoppingTime ℱ τ", content)
        self.assertIn("MeasurableSet[ℱ i] {ω | τ ω ≤ i}", content)
        self.assertIn("hτ.measurableSet_le i", content)
        self.assertNotIn("by sorry", content)

    def test_submartingale_optional_stopping_bridge_supports_sequential_gap(self) -> None:
        obligation = get_obligation("submartingale_expected_stopped_value_mono")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("stopping_time_le_event_measurable",))
        self.assertIn("submartingale", obligation.tags)
        self.assertIn("optional_stopping", obligation.tags)
        self.assertIn("nonnegative_supermartingale", obligation.tags)
        self.assertIn("theorem submartingale_expected_stoppedValue_mono_bridge", content)
        self.assertIn("Submartingale f 𝒢 μ", content)
        self.assertIn("IsStoppingTime 𝒢 τ", content)
        self.assertIn("μ[stoppedValue f τ] ≤ μ[stoppedValue f π]", content)
        self.assertIn("hf.expected_stoppedValue_mono hτ hπ hle hbdd", content)
        self.assertNotIn("by sorry", content)

    def test_submartingale_stopped_process_bridge_supports_sequential_gap(self) -> None:
        obligation = get_obligation("submartingale_stopped_process")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("submartingale_expected_stopped_value_mono",))
        self.assertIn("submartingale", obligation.tags)
        self.assertIn("stopped_process", obligation.tags)
        self.assertIn("nonnegative_supermartingale", obligation.tags)
        self.assertIn("theorem submartingale_stoppedProcess_bridge", content)
        self.assertIn("Submartingale f 𝒢 μ", content)
        self.assertIn("Submartingale (stoppedProcess f τ) 𝒢 μ", content)
        self.assertIn("hf.stoppedProcess hτ", content)
        self.assertNotIn("by sorry", content)

    def test_submartingale_doob_maximal_bridge_supports_ville_gap(self) -> None:
        obligation = get_obligation("submartingale_doob_maximal_ineq")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("submartingale_stopped_process", "submartingale_expected_stopped_value_mono"),
        )
        self.assertIn("maximal_inequality", obligation.tags)
        self.assertIn("doob", obligation.tags)
        self.assertIn("ville_inequality", obligation.tags)
        self.assertIn("nonnegative_supermartingale", obligation.tags)
        self.assertIn("eprocess_type1_control", obligation.tags)
        self.assertIn("theorem submartingale_doob_maximal_ineq_bridge", content)
        self.assertIn("Submartingale f 𝒢 μ", content)
        self.assertIn("0 ≤ f", content)
        self.assertIn("range (n + 1)", content)
        self.assertIn("maximal_ineq hsub hnonneg n", content)
        self.assertNotIn("by sorry", content)

    def test_supermartingale_optional_stopping_bridge_supports_eprocess_gap(self) -> None:
        obligation = get_obligation("supermartingale_expected_stopped_value_antimono")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("submartingale_expected_stopped_value_mono",))
        self.assertIn("supermartingale", obligation.tags)
        self.assertIn("expectation_budget", obligation.tags)
        self.assertIn("ville_inequality", obligation.tags)
        self.assertIn("eprocess_type1_control", obligation.tags)
        self.assertIn("theorem supermartingale_expected_stoppedValue_antimono_bridge", content)
        self.assertIn("Supermartingale f 𝒢 μ", content)
        self.assertIn("μ[stoppedValue f π] ≤ μ[stoppedValue f τ]", content)
        self.assertIn("hf.setIntegral_le", content)
        self.assertIn("stoppedValue_sub_eq_sum' hle hbdd", content)
        self.assertNotIn("by sorry", content)

    def test_submartingale_doob_budget_bridge_supports_eprocess_gap(self) -> None:
        obligation = get_obligation("submartingale_doob_maximal_budget")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("submartingale_doob_maximal_ineq",))
        self.assertIn("maximal_inequality", obligation.tags)
        self.assertIn("budget", obligation.tags)
        self.assertIn("ville_inequality", obligation.tags)
        self.assertIn("eprocess_type1_control", obligation.tags)
        self.assertIn("theorem submartingale_doob_maximal_budget_bridge", content)
        self.assertIn("hbudget", content)
        self.assertIn("ε * α", content)
        self.assertIn("le_trans (maximal_ineq hsub hnonneg n) hbudget", content)
        self.assertNotIn("by sorry", content)

    def test_submartingale_doob_probability_bound_supports_eprocess_gap(self) -> None:
        obligation = get_obligation("submartingale_doob_maximal_probability_bound")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("submartingale_doob_maximal_budget",))
        self.assertIn("probability_bound", obligation.tags)
        self.assertIn("cancellation", obligation.tags)
        self.assertIn("ville_inequality", obligation.tags)
        self.assertIn("eprocess_type1_control", obligation.tags)
        self.assertIn("theorem submartingale_doob_maximal_probability_bound_bridge", content)
        self.assertIn("hε : ε ≠ 0", content)
        self.assertIn("μ {ω |", content)
        self.assertIn("≤ α", content)
        self.assertIn("ENNReal.mul_le_mul_iff_right", content)
        self.assertIn("exact_mod_cast hε", content)
        self.assertNotIn("by sorry", content)

    def test_submartingale_ae_tendsto_limit_process_supports_survival_gap(self) -> None:
        obligation = get_obligation("submartingale_ae_tendsto_limit_process")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("submartingale_expected_stopped_value_mono",))
        self.assertIn("submartingale", obligation.tags)
        self.assertIn("convergence", obligation.tags)
        self.assertIn("survival_martingale_clt", obligation.tags)
        self.assertIn("theorem submartingale_ae_tendsto_limitProcess_bridge", content)
        self.assertIn("Submartingale f 𝒢 μ", content)
        self.assertIn("eLpNorm (f n) 1 μ ≤ R", content)
        self.assertIn("∀ᵐ ω ∂μ, Tendsto", content)
        self.assertIn("hf.ae_tendsto_limitProcess hbdd", content)
        self.assertNotIn("by sorry", content)

    def test_submartingale_l1_tendsto_limit_process_supports_survival_gap(self) -> None:
        obligation = get_obligation("submartingale_l1_tendsto_limit_process")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("submartingale_ae_tendsto_limit_process",))
        self.assertIn("submartingale", obligation.tags)
        self.assertIn("l1_convergence", obligation.tags)
        self.assertIn("uniform_integrability", obligation.tags)
        self.assertIn("survival_martingale_clt", obligation.tags)
        self.assertIn("theorem submartingale_tendsto_eLpNorm_one_limitProcess_bridge", content)
        self.assertIn("UniformIntegrable f 1 μ", content)
        self.assertIn("Tendsto (fun n => eLpNorm", content)
        self.assertIn("hf.tendsto_eLpNorm_one_limitProcess hunif", content)
        self.assertNotIn("by sorry", content)

    def test_martingale_ae_eq_condexp_limit_process_supports_martingale_gaps(self) -> None:
        obligation = get_obligation("martingale_ae_eq_condexp_limit_process")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("submartingale_l1_tendsto_limit_process",))
        self.assertIn("martingale", obligation.tags)
        self.assertIn("conditional_expectation", obligation.tags)
        self.assertIn("uniform_integrability", obligation.tags)
        self.assertIn("survival_martingale_clt", obligation.tags)
        self.assertIn("martingale_definition", obligation.tags)
        self.assertIn("theorem martingale_ae_eq_condExp_limitProcess_bridge", content)
        self.assertIn("Martingale f 𝒢 μ", content)
        self.assertIn("μ[𝒢.limitProcess f μ | 𝒢 n]", content)
        self.assertIn("hf.ae_eq_condExp_limitProcess hunif n", content)
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

    def test_wald_interval_obligation_links_containment_to_absolute_error(self) -> None:
        obligation = get_obligation("wald_interval_contains_iff_abs_error")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem waldInterval_contains_iff_abs_error", content)
        self.assertIn("estimate - radius ≤ theta", content)
        self.assertIn("theta ≤ estimate + radius", content)
        self.assertIn("|estimate - theta| ≤ radius", content)
        self.assertIn("abs_le", content)
        self.assertIn("linarith", content)
        self.assertIn("coverage", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_wald_interval_miscoverage_obligation_links_miss_to_tail_event(self) -> None:
        obligation = get_obligation("wald_interval_miscoverage_iff_abs_error_gt")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("wald_interval_contains_iff_abs_error",))
        self.assertIn("theorem waldInterval_miscoverage_iff_abs_error_gt", content)
        self.assertIn("¬ (estimate - radius ≤ theta ∧ theta ≤ estimate + radius)", content)
        self.assertIn("radius < |estimate - theta|", content)
        self.assertIn("le_of_not_gt", content)
        self.assertIn("not_le_of_gt", content)
        self.assertIn("miscoverage", obligation.tags)
        self.assertIn("tail_event", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_coverage_lower_bound_obligation_uses_complement_error_control(self) -> None:
        obligation = get_obligation("coverage_lower_bound_of_complement_error")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("prob_compl",))
        self.assertIn("theorem coverageLowerBound_of_complement_error", content)
        self.assertIn("μ Aᶜ ≤ α", content)
        self.assertIn("1 - α ≤ μ A", content)
        self.assertIn("prob_compl_eq_one_sub", content)
        self.assertIn("tsub_le_tsub_left", content)
        self.assertIn("miscoverage", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_simultaneous_coverage_obligation_composes_union_error_bound(self) -> None:
        obligation = get_obligation("simultaneous_coverage_of_union_error_bound")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("finite_union_budget_control", "coverage_lower_bound_of_complement_error"),
        )
        self.assertIn("theorem simultaneousCoverage_of_union_error_bound", content)
        self.assertIn("μ (⋃ i ∈ I, A i) ≤ α", content)
        self.assertIn("1 - α ≤ μ (⋃ i ∈ I, A i)ᶜ", content)
        self.assertIn("prob_compl_eq_one_sub", content)
        self.assertIn("tsub_le_tsub_left", content)
        self.assertIn("simultaneous_coverage", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_finite_conformal_rank_coverage_counting_uses_bad_rank_union(self) -> None:
        obligation = get_obligation("finite_conformal_rank_coverage_counting")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "simultaneous_coverage_of_union_error_bound",
                "coverage_lower_bound_of_complement_error",
                "finite_union_budget_control",
            ),
        )
        self.assertIn("theorem finiteConformalRank_coverage_counting", content)
        self.assertIn("BadRanks : Finset ρ", content)
        self.assertIn("rank : Ω → ρ", content)
        self.assertIn("μ {ω | rank ω = r} ≤ α r", content)
        self.assertIn("1 - α_total ≤ μ ({ω | rank ω ∈ BadRanks}ᶜ)", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("prob_compl_eq_one_sub", content)
        self.assertIn("finite_sample_coverage_counting", obligation.tags)
        self.assertIn("rank_uniformity", obligation.tags)
        self.assertIn("order_statistic_quantile_rule", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_finite_family_error_union_control_supports_simultaneous_bands(self) -> None:
        obligation = get_obligation("finite_family_absolute_error_union_control")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("finite_union_budget_control",))
        self.assertIn("theorem finiteFamily_absolute_error_union_control", content)
        self.assertIn("radius i ≤ |X i ω - theta i|", content)
        self.assertIn("μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|})", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("Finset.sum_le_sum", content)
        self.assertIn("simultaneous_confidence_bands", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_finite_family_absolute_error_coverage_composes_union_and_complement(self) -> None:
        obligation = get_obligation("finite_family_absolute_error_simultaneous_coverage")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "finite_family_absolute_error_union_control",
                "simultaneous_coverage_of_union_error_bound",
                "coverage_lower_bound_of_complement_error",
            ),
        )
        self.assertIn("theorem finiteFamily_absolute_error_simultaneous_coverage", content)
        self.assertIn("1 - α_total ≤ μ (⋃ i ∈ I, {ω | radius i ≤ |X i ω - theta i|})ᶜ", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("Finset.sum_le_sum", content)
        self.assertIn("prob_compl_eq_one_sub", content)
        self.assertIn("tsub_le_tsub_left", content)
        self.assertIn("simultaneous_confidence_bands", obligation.tags)
        self.assertIn("miscoverage", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_pairwise_top_rank_bridge_uses_separation_and_error_bounds(self) -> None:
        obligation = get_obligation("pairwise_top_rank_correct_of_separation")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("wald_interval_contains_iff_abs_error",))
        self.assertIn("theorem pairwiseTopRank_correct_of_separation", content)
        self.assertIn("theta_j + 2 * radius < theta_i", content)
        self.assertIn("|estimate_i - theta_i| ≤ radius", content)
        self.assertIn("|estimate_j - theta_j| ≤ radius", content)
        self.assertIn("estimate_j < estimate_i", content)
        self.assertIn("abs_le.mp", content)
        self.assertIn("linarith", content)
        self.assertIn("pairwise_country_mean_separation", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_top_rank_correct_obligation_uses_uniform_error_separation(self) -> None:
        obligation = get_obligation("top_rank_correct_of_uniform_error_separation")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "pairwise_top_rank_correct_of_separation",
                "finite_family_absolute_error_simultaneous_coverage",
            ),
        )
        self.assertIn("theorem topRank_correct_of_uniform_error_separation", content)
        self.assertIn("∀ j, j ≠ i → theta j + 2 * radius < theta i", content)
        self.assertIn("∀ j, |estimate j - theta j| ≤ radius", content)
        self.assertIn("∀ j, j ≠ i → estimate j < estimate i", content)
        self.assertIn("abs_le.mp", content)
        self.assertIn("linarith", content)
        self.assertIn("selection", obligation.tags)
        self.assertIn("finite_sample", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_finite_union_bound_obligation_uses_mathlib_bonferroni_lemma(self) -> None:
        obligation = get_obligation("finite_union_bound")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertIn("theorem finite_union_bound", content)
        self.assertIn("μ (⋃ i ∈ I, A i)", content)
        self.assertIn("∑ i ∈ I, μ (A i)", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertNotIn("by sorry", content)

    def test_selected_bad_event_bridge_controls_data_dependent_selection(self) -> None:
        obligation = get_obligation("selected_bad_event_probability_le_finite_union_budget")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("finite_union_bound", "finite_union_budget_control", "event_probability_mono"),
        )
        self.assertIn("theorem selectedBadEvent_probability_le_finite_union_budget", content)
        self.assertIn("select : Ω → ι", content)
        self.assertIn("μ {ω | ω ∈ B (select ω)} ≤ α_total", content)
        self.assertIn("measure_mono", content)
        self.assertIn("Set.mem_iUnion.mpr", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("Finset.sum_le_sum", content)
        self.assertIn("post_selection", obligation.tags)
        self.assertIn("adaptive_selection", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_selected_good_event_coverage_bridge_uses_complement_budget(self) -> None:
        obligation = get_obligation("selected_good_event_coverage_of_finite_union_budget")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "selected_bad_event_probability_le_finite_union_budget",
                "coverage_lower_bound_of_complement_error",
                "finite_union_budget_control",
            ),
        )
        self.assertIn("theorem selectedGoodEvent_coverage_of_finite_union_budget", content)
        self.assertIn("hSelectedBad : MeasurableSet {ω | ω ∈ B (select ω)}", content)
        self.assertIn("1 - α_total ≤ μ ({ω | ω ∈ B (select ω)}ᶜ)", content)
        self.assertIn("measure_mono", content)
        self.assertIn("prob_compl_eq_one_sub", content)
        self.assertIn("tsub_le_tsub_left", content)
        self.assertIn("selected_interval", obligation.tags)
        self.assertIn("confidence_set", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_sequential_elimination_rule_bridge_controls_selected_bad_event(self) -> None:
        obligation = get_obligation("sequential_elimination_rule_finite_union_control")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "selected_bad_event_probability_le_finite_union_budget",
                "finite_union_budget_control",
                "finite_union_bound",
            ),
        )
        self.assertIn("theorem sequentialEliminationRule_finite_union_control", content)
        self.assertIn("eliminate : Ω → ι", content)
        self.assertIn("μ {ω | ω ∈ Bad (eliminate ω)} ≤ α_total", content)
        self.assertIn("measure_mono", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("Finset.sum_le_sum", content)
        self.assertIn("sequential_elimination_rule", obligation.tags)
        self.assertIn("model_confidence_set", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_finite_null_family_no_false_rejection_bridge_uses_union_and_complement(self) -> None:
        obligation = get_obligation("finite_null_family_no_false_rejection_probability")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "finite_union_budget_control",
                "simultaneous_coverage_of_union_error_bound",
                "prob_compl",
            ),
        )
        self.assertIn("theorem finiteNullFamily_noFalseRejection_probability", content)
        self.assertIn("1 - α_total ≤ μ (⋃ i ∈ I, R i)ᶜ", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("Finset.sum_le_sum", content)
        self.assertIn("prob_compl_eq_one_sub", content)
        self.assertIn("tsub_le_tsub_left", content)
        self.assertIn("familywise_error", obligation.tags)
        self.assertIn("false_rejection", obligation.tags)
        self.assertIn("fdr", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_finite_null_pvalue_no_false_rejection_bridge_uses_validity_budget(self) -> None:
        obligation = get_obligation("finite_null_pvalue_no_false_rejection_probability")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "finite_null_family_no_false_rejection_probability",
                "finite_union_budget_control",
                "prob_compl",
            ),
        )
        self.assertIn("theorem finiteNullPValue_noFalseRejection_probability", content)
        self.assertIn("p : ι → Ω → ENNReal", content)
        self.assertIn("μ {ω | p i ω ≤ τ i} ≤ τ i", content)
        self.assertIn("1 - α_total ≤ μ (⋃ i ∈ I, {ω | p i ω ≤ τ i})ᶜ", content)
        self.assertIn("measure_biUnion_finset_le", content)
        self.assertIn("prob_compl_eq_one_sub", content)
        self.assertIn("valid_null_pvalue_uniformity", obligation.tags)
        self.assertIn("ordered_pvalues", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_bh_threshold_grid_mono_uses_gcongr_threshold_algebra(self) -> None:
        obligation = get_obligation("bh_threshold_grid_mono")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("finite_null_pvalue_no_false_rejection_probability",))
        self.assertIn("noncomputable def bhThreshold", content)
        self.assertIn("q * (k : ℝ) / (m : ℝ)", content)
        self.assertIn("theorem bhThreshold_grid_mono", content)
        self.assertIn("bhThreshold q m k ≤ bhThreshold q m l", content)
        self.assertIn("unfold bhThreshold", content)
        self.assertIn("gcongr", content)
        self.assertIn("bh_threshold_fixed_point", obligation.tags)
        self.assertIn("bh_stepup_self_consistency", obligation.tags)
        self.assertIn("ordered_pvalues", obligation.tags)
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

    def test_independent_null_event_family_bridge_uses_iindep_inter_product(self) -> None:
        obligation = get_obligation("independent_null_event_family_inter_probability")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("independent_event_inter_probability",))
        self.assertIn("theorem independentFiniteEventInter_probability", content)
        self.assertIn("iIndepSet A μ", content)
        self.assertIn("μ (⋂ i ∈ I, A i) = ∏ i ∈ I, μ (A i)", content)
        self.assertIn("iIndepSet.meas_biInter", content)
        self.assertIn("null_pvalues", obligation.tags)
        self.assertIn("fdr", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_independent_null_event_complement_family_bridge_uses_generated_sigma_algebra(self) -> None:
        obligation = get_obligation("independent_null_event_family_compl_inter_probability")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("independent_null_event_family_inter_probability", "prob_compl"),
        )
        self.assertIn("theorem independentFiniteEventComplInter_probability", content)
        self.assertIn("iIndepSet A μ", content)
        self.assertIn("μ (⋂ i ∈ I, (A i)ᶜ) = ∏ i ∈ I, μ (A i)ᶜ", content)
        self.assertIn("iIndepSet_iff", content)
        self.assertIn("MeasurableSpace.measurableSet_generateFrom", content)
        self.assertIn("familywise_error", obligation.tags)
        self.assertIn("null_pvalues", obligation.tags)
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

    def test_event_indicator_product_integral_bridge_uses_intersection_indicator(self) -> None:
        obligation = get_obligation("event_indicator_product_integral_eq_inter")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("event_indicator_expectation",))
        self.assertIn("theorem eventIndicatorProduct_integral_eq_inter", content)
        self.assertIn("A.indicator (1 : Ω → ℝ) * B.indicator (1 : Ω → ℝ)", content)
        self.assertIn("μ.real (A ∩ B)", content)
        self.assertIn("Set.inter_indicator_one", content)
        self.assertIn("integral_indicator_one", content)
        self.assertIn("adapted_product_process", obligation.tags)
        self.assertIn("conditional_expectation_product_step", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_independent_event_indicator_product_lintegral_factors_under_independence(self) -> None:
        obligation = get_obligation("independent_event_indicator_product_lintegral_eq_mul")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            ("event_indicator_product_integral_eq_inter", "independent_event_inter_probability"),
        )
        self.assertIn("theorem independentEventIndicatorProduct_lintegral_eq_mul", content)
        self.assertIn("IndepSet A B μ", content)
        self.assertIn("∫⁻ ω, (A.indicator (1 : Ω → ENNReal) * B.indicator (1 : Ω → ENNReal)) ω ∂μ", content)
        self.assertIn("μ A * μ B", content)
        self.assertIn("Set.inter_indicator_one", content)
        self.assertIn("lintegral_indicator_one", content)
        self.assertIn("h_indep.measure_inter_eq_mul", content)
        self.assertIn("independent_bernoulli_sequence", obligation.tags)
        self.assertIn("martingale_definition", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_independent_event_indicator_condexp_filtration_bridge_uses_mathlib_borel_cantelli(self) -> None:
        obligation = get_obligation("independent_event_indicator_condExp_filtration_eq_prob")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "event_indicator_expectation",
                "filtration_mono_measurable_set",
                "independent_event_indicator_product_lintegral_eq_mul",
            ),
        )
        self.assertIn("theorem independentSet_indicator_condExp_filtrationOfSet_ae_eq", content)
        self.assertIn("iIndepSet s μ", content)
        self.assertIn("filtrationOfSet hsm i", content)
        self.assertIn("=ᵐ[μ]", content)
        self.assertIn("fun _ => μ.real (s j)", content)
        self.assertIn("hs.condExp_indicator_filtrationOfSet_ae_eq hsm hij", content)
        self.assertIn("conditional_expectation_product_step", obligation.tags)
        self.assertIn("martingale_definition", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_independent_real_condexp_natural_bridge_uses_mathlib_borel_cantelli(self) -> None:
        obligation = get_obligation("independent_real_condExp_natural_eq_mean")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("filtration_mono_measurable_set",))
        self.assertIn("theorem independentReal_condExp_natural_ae_eq_of_lt", content)
        self.assertIn("X : ℕ → Ω → ℝ", content)
        self.assertIn("iIndepFun X μ", content)
        self.assertIn("Filtration.natural X hX i", content)
        self.assertIn("=ᵐ[μ] fun _ => μ[X j]", content)
        self.assertIn("h_ind.condExp_natural_ae_eq_of_lt hX hij", content)
        self.assertIn("iid_empirical_mean_clt", obligation.tags)
        self.assertIn("sample_moment_lln", obligation.tags)
        self.assertIn("exogeneity_moment_condition", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_iid_real_clt_bridge_uses_mathlib_central_limit_theorem(self) -> None:
        obligation = get_obligation("iid_real_clt_tendsto_distribution")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "independent_real_condExp_natural_eq_mean",
                "finite_sample_mean_variance_indep",
                "variance_nonneg",
            ),
        )
        self.assertIn("theorem iidReal_tendstoInDistribution_inv_sqrt_sum_sub", content)
        self.assertIn("HasLaw Y (gaussianReal 0 Var[X 0; P].toNNReal) P'", content)
        self.assertIn("MemLp (X 0) 2 P", content)
        self.assertIn("iIndepFun X P", content)
        self.assertIn("IdentDistrib (X i) (X 0) P P", content)
        self.assertIn("TendstoInDistribution", content)
        self.assertIn("tendstoInDistribution_inv_sqrt_mul_sum_sub hY hX hindep hident", content)
        self.assertIn("iid_empirical_mean_clt", obligation.tags)
        self.assertIn("asymptotic_normality", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_continuous_mapping_bridge_uses_mathlib_tendsto_in_distribution(self) -> None:
        obligation = get_obligation("tendsto_in_distribution_continuous_mapping")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(obligation.depends_on, ("iid_real_clt_tendsto_distribution",))
        self.assertIn("theorem tendstoInDistribution_continuousMapping_bridge", content)
        self.assertIn("TendstoInDistribution X l Z μ μ'", content)
        self.assertIn("Continuous g", content)
        self.assertIn("TendstoInDistribution (fun i => g ∘ X i)", content)
        self.assertIn("h.continuous_comp hg", content)
        self.assertIn("continuous_mapping", obligation.tags)
        self.assertIn("delta_method", obligation.tags)
        self.assertNotIn("by sorry", content)

    def test_slutsky_add_negligible_zero_bridge_uses_mathlib_tendsto_in_measure(self) -> None:
        obligation = get_obligation("slutsky_add_negligible_zero_real")
        content = splice_proof(obligation.formal_statement, obligation.proof_body)
        self.assertEqual(
            obligation.depends_on,
            (
                "iid_real_clt_tendsto_distribution",
                "tendsto_in_distribution_continuous_mapping",
            ),
        )
        self.assertIn("theorem real_slutsky_add_negligible_zero", content)
        self.assertIn("TendstoInMeasure sampleLaw remainder l", content)
        self.assertIn("hmain.add_of_tendstoInMeasure_const", content)
        self.assertIn("(c := (0 : ℝ))", content)
        self.assertIn("slutsky", obligation.tags)
        self.assertIn("negligible_remainder", obligation.tags)
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
    def test_evaluation_benchmark_guidance_flags_capacity_gaps(self) -> None:
        payload = {
            "gates": {"release": True},
            "counts": {
                "questions": 10,
                "frontier_questions": 60,
                "frontier_supported": 60,
                "frontier_precision_flagged": 0,
                "frontier_smoke_questions": 23,
                "frontier_theory_expected_result_coverage_rate": 0.86,
                "research_ready_with_gaps": 10,
                "research_simulation_flagged": 0,
                "formal_gaps": 20,
                "formalized_gaps": 20,
                "missing_formal_primitives": 97,
                "primitive_source_coverage_direct_wrapper_possible": 32,
                "primitive_source_coverage_bridge_lemma_needed": 41,
                "primitive_source_coverage_source_only_not_importable": 18,
                "primitive_source_coverage_no_source_found": 6,
                "proofs_kernel_verified": 92,
                "proof_search_solved": 12,
                "proof_search_obligations": 12,
                "proof_search_retrieval_ablation_candidate_delta": 0,
                "lean_rag_dependency_graph_enabled": True,
                "research_algorithms_ok": 33,
                "research_algorithms_total": 33,
                "algorithm_simulation_stress_cases": 30,
                "algorithm_simulation_stress_seeds": 3,
                "algorithm_simulation_stress_all_passed": True,
                "algorithm_simulation_stress_all_finite_metrics": True,
                "algorithm_simulation_stress_all_stress_ledgers_ok": True,
                "algorithm_simulation_stress_all_diagnoses_ok": True,
                "algorithm_simulation_stress_multi_seed_checked": True,
                "research_loop_theory_revisions": 6,
                "algorithm_repair_sandbox_patch_eval_promotion_ready": 0,
                "adversarial_intake_cases": 6,
                "adversarial_intake_ok": 6,
                "adversarial_intake_rejected": 6,
                "fresh_holdout_frontier_entries": 6,
                "fresh_holdout_frontier_supported": 4,
                "fresh_holdout_frontier_unsupported": 2,
                "fresh_holdout_frontier_scored_traces": 4,
                "fresh_holdout_frontier_expected_results": 12,
                "fresh_holdout_frontier_expected_results_covered": 8,
                "fresh_holdout_frontier_expected_result_coverage_rate": 0.667,
                "fresh_holdout_frontier_identity_withheld": True,
                "fresh_holdout_frontier_source_leakage_detected": False,
                "fresh_holdout_frontier_all_ok": True,
            },
            "artifacts": {
                "research_benchmark": "runs/example/research_benchmark_manifest.json",
                "frontier_coverage_audit": "runs/example/frontier_coverage_manifest.json",
                "frontier_precision_audit": "runs/example/frontier_precision_manifest.json",
                "frontier_smoke_benchmark": "runs/example/frontier_smoke_manifest.json",
                "formalization_target_audit": "runs/example/formalization_target_manifest.json",
                "proof_bank_expansion": "runs/example/proof_bank_expansion_manifest.json",
                "primitive_source_coverage": "runs/example/primitive_source_coverage_manifest.json",
                "proof_audit": "runs/example/proof_audit_manifest.json",
                "proof_search_audit": "runs/example/proof_search_audit_manifest.json",
                "proof_search_retrieval_ablation": "runs/example/proof_search_retrieval_ablation_manifest.json",
                "research_algorithm_audit": "runs/example/research_algorithm_audit_manifest.json",
                "algorithm_simulation_stress_audit": "runs/example/algorithm_simulation_stress_manifest.json",
                "research_loop": "runs/example/research_loop_manifest.json",
                "research_loop_repair_audit": "runs/example/research_loop_repair_audit_manifest.json",
                "algorithm_repair_sandbox_patch_eval": "runs/example/algorithm_repair_sandbox_patch_eval_manifest.json",
                "adversarial_intake_audit": "runs/example/adversarial_intake_manifest.json",
                "fresh_holdout_frontier_audit": "runs/example/fresh_holdout_frontier_manifest.json",
            },
        }
        guidance = build_evaluation_benchmark_guidance(
            Path("runs/test_evaluation_benchmark_guidance"),
            system_audit_payload=payload,
        )
        self.assertTrue(guidance["all_ok"])
        self.assertEqual(guidance["suites_defined"], 10)
        self.assertEqual(guidance["frontier_entries"], 60)
        statuses = {row["suite_id"]: row["status"] for row in guidance["suites"]}
        self.assertEqual(statuses["S3_frontier_blind_theory_target"], "CAPACITY_GAP")
        self.assertEqual(statuses["S4_formal_primitive_ladder"], "CAPACITY_GAP")
        self.assertEqual(statuses["S5_proof_bank_and_search"], "SATURATED")
        self.assertEqual(statuses["S6_algorithm_simulation_stress"], "OK")
        self.assertEqual(statuses["S8_adversarial_unsupported_intake"], "OK")
        self.assertEqual(statuses["S9_fresh_holdout_frontier"], "OK")
        self.assertGreaterEqual(len(guidance["top_actions"]), 3)
        self.assertTrue(
            Path(
                "runs/test_evaluation_benchmark_guidance/"
                "evaluation_benchmark_guidance_manifest.json"
            ).exists()
        )
        self.assertTrue(
            Path("runs/test_evaluation_benchmark_guidance/evaluation_benchmark_guidance.md").exists()
        )

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
        self.assertEqual(payload["n_algorithms"], 33)
        self.assertEqual(len(payload["registry_fingerprint"]), 64)
        for row in payload["algorithms"]:
            self.assertEqual(row["registry_status"], "vetted")
            self.assertEqual(len(row["implementation_hash"]), 64)
        self.assertTrue(Path("runs/test_research_algorithm_audit/research_algorithm_audit_manifest.json").exists())

    def test_algorithm_simulation_stress_audit_checks_multiseed_stress_ledgers(self) -> None:
        payload = audit_algorithm_simulation_stress(
            Path("runs/test_algorithm_simulation_stress_audit"),
            seeds=(31, 32),
            n_runs=10,
            max_questions=2,
        )
        self.assertTrue(payload["all_ok"])
        self.assertTrue(payload["multi_seed_stability_checked"])
        self.assertEqual(payload["n_seeds"], 2)
        self.assertEqual(payload["n_questions"], 2)
        self.assertGreaterEqual(payload["n_seeded_simulations"], 3)
        self.assertTrue(payload["all_finite_metrics"])
        self.assertTrue(payload["all_stress_ledgers_ok"])
        self.assertTrue(payload["all_diagnoses_ok"])
        self.assertTrue(Path("runs/test_algorithm_simulation_stress_audit/algorithm_simulation_stress_manifest.json").exists())
        self.assertTrue(Path("runs/test_algorithm_simulation_stress_audit/algorithm_simulation_stress.md").exists())

    def test_fresh_holdout_frontier_audit_runs_source_withheld_traces(self) -> None:
        async def run():
            return await audit_fresh_holdout_frontier(
                Path("runs/test_fresh_holdout_frontier_audit"),
                n_runs=10,
                seed=20260601,
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_entries"], 6)
        self.assertGreaterEqual(payload["n_supported"], 1)
        self.assertGreaterEqual(payload["n_scored_traces"], 1)
        self.assertTrue(payload["all_prompt_identity_withheld"])
        self.assertFalse(payload["source_identity_leakage_detected"])
        self.assertFalse(payload["overlap_with_main_frontier_ids"])
        self.assertEqual(payload["missing_required_fields"], [])
        self.assertGreater(payload["n_expected_results"], 0)
        self.assertTrue(Path("runs/test_fresh_holdout_frontier_audit/fresh_holdout_frontier_manifest.json").exists())
        self.assertTrue(Path("runs/test_fresh_holdout_frontier_audit/fresh_holdout_frontier.md").exists())

    def test_research_intake_audit_accepts_supported_and_rejects_unsupported(self) -> None:
        payload = audit_research_question_intake(Path("runs/test_research_intake_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_supported"], 21)
        self.assertEqual(payload["n_supported_accepted"], 21)
        self.assertEqual(payload["n_unsupported"], 3)
        self.assertEqual(payload["n_unsupported_rejected"], 3)
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
                "sequential_changepoint_inference",
                "high_dimensional_pca_inference",
                "extreme_tail_quantile_inference",
            },
        )
        self.assertTrue(Path("runs/test_research_intake_audit/research_intake_audit_manifest.json").exists())

    def test_adversarial_unsupported_intake_audit_rejects_overclaiming_prompts(self) -> None:
        payload = audit_adversarial_unsupported_intake(Path("runs/test_adversarial_intake_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_cases"], 6)
        self.assertEqual(payload["n_ok"], payload["n_cases"])
        self.assertEqual(payload["n_rejected"], payload["n_cases"])
        risks = set(payload["by_risk"])
        self.assertIn("gold_answer_leakage", risks)
        self.assertIn("prompt_injection", risks)
        self.assertTrue(Path("runs/test_adversarial_intake_audit/adversarial_intake_manifest.json").exists())
        self.assertTrue(Path("runs/test_adversarial_intake_audit/adversarial_intake.md").exists())

    def test_research_knowledge_audit_checks_sources_and_problem_retrieval(self) -> None:
        payload = audit_research_knowledge(Path("runs/test_research_knowledge_audit"))
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_cards"], payload["n_source_ok"])
        self.assertTrue(payload["source_inventory"]["all_ok"])
        self.assertEqual(payload["source_inventory"]["n_ok"], payload["source_inventory"]["n_sources"])
        self.assertEqual(len(payload["source_inventory"]["inventory_fingerprint"]), 64)
        source_card_ids = {row["card_id"] for row in payload["source_rows"]}
        self.assertIn("leansearch_client_local", source_card_ids)
        self.assertIn("leandojo_v2_local", source_card_ids)
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
        source_inventory = json.loads(
            Path("runs/test_research_knowledge_audit/source_inventory/research_source_inventory_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        source_inventory_ids = {row["source_id"] for row in source_inventory["rows"]}
        self.assertIn("leansearch_client", source_inventory_ids)
        self.assertIn("leandojo_v2_local", source_inventory_ids)
        self.assertIn("atlas_lean_repository", source_inventory_ids)
        self.assertIn("atlas_lean_high_dimensional_statistics", source_inventory_ids)
        self.assertIn("atlas_lean_fourier_analysis", source_inventory_ids)
        self.assertIn("atlas_lean_functional_analysis", source_inventory_ids)
        self.assertIn("atlas_lean_differential_analysis", source_inventory_ids)
        self.assertIn("atlas_lean_projection_theory", source_inventory_ids)
        self.assertIn("formal_slt", source_inventory_ids)
        self.assertIn("lean_rademacher", source_inventory_ids)
        self.assertIn("lean_machine_learning_lml", source_inventory_ids)
        self.assertIn("brownian_motion_lean", source_inventory_ids)
        self.assertIn("kolmogorov_extension_lean", source_inventory_ids)
        self.assertIn("scilean_calculus", source_inventory_ids)
        atlas_rows = [row for row in source_inventory["rows"] if str(row["source_id"]).startswith("atlas_lean")]
        self.assertTrue(atlas_rows)
        self.assertTrue(all(row["usage_policy"] == "retrieval_only_no_training_export" for row in atlas_rows))
        self.assertTrue(all(row["git_commit"] for row in atlas_rows))
        brownian = next(row for row in source_inventory["rows"] if row["source_id"] == "brownian_motion_lean")
        scilean = next(row for row in source_inventory["rows"] if row["source_id"] == "scilean_calculus")
        self.assertEqual(brownian["usage_policy"], "retrieval_only_no_training_export")
        self.assertEqual(scilean["usage_policy"], "retrieval_only_no_training_export")
        self.assertTrue(brownian["git_commit"])
        self.assertTrue(scilean["git_commit"])
        self.assertIn("autoform_bot_harness", source_inventory_ids)
        autoform = next(row for row in source_inventory["rows"] if row["source_id"] == "autoform_bot_harness")
        self.assertEqual(autoform["usage_policy"], "integration_reference_no_training_export")
        self.assertTrue(autoform["git_commit"])

    def test_autoform_harness_audit_detects_reusable_framework(self) -> None:
        payload = audit_autoform_harness(Path("runs/test_autoform_harness"))
        self.assertTrue(payload["ready_for_integration"])
        profile = payload["profile"]
        self.assertTrue(profile["has_statement_extraction"])
        self.assertTrue(profile["has_lean_eval"])
        self.assertTrue(profile["has_dependency_graph_eval"])
        self.assertTrue(profile["has_lean_proof_checker"])
        self.assertTrue(profile["has_lean_repl_tool"])
        self.assertTrue(profile["has_native_lsp_tool"])
        self.assertTrue(profile["has_lean_skill_docs"])
        self.assertEqual(profile["usage_policy"], "integration_reference_no_training_export")
        self.assertTrue(Path("runs/test_autoform_harness/autoform_harness_manifest.json").exists())
        from ai_statistician.cli import build_parser

        args = build_parser().parse_args(
            ["autoform-harness-audit", "--out", "runs/test_autoform_harness_cli"]
        )
        self.assertEqual(args.func(args), 0)
        self.assertTrue(Path("runs/test_autoform_harness_cli/autoform_harness_manifest.json").exists())

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
        self.assertEqual(payload["n_supported"], 60)
        self.assertEqual(payload["n_unsupported"], 0)
        self.assertEqual(payload["by_problem_class"]["experimental_design_optimization"], 3)
        self.assertEqual(payload["by_problem_class"]["network_graph_inference"], 5)
        self.assertEqual(payload["by_problem_class"]["sequential_changepoint_inference"], 3)
        self.assertEqual(payload["by_problem_class"]["geometric_spatial_point_process_inference"], 6)
        self.assertEqual(payload["by_problem_class"]["high_dimensional_latent_structure_inference"], 3)
        self.assertEqual(payload["by_problem_class"]["adaptive_transfer_active_preference_learning"], 3)
        self.assertEqual(payload["by_problem_class"]["robust_distributed_model_privacy_inference"], 3)
        self.assertEqual(payload["by_problem_class"]["heavy_tail_time_series_extremal_dependence"], 3)
        self.assertEqual(payload["by_problem_class"]["bayesian_tree_mcmc_computation"], 2)
        self.assertEqual(payload["by_problem_class"]["missing_mediation_deconvolution_inference"], 2)
        self.assertNotIn("unsupported_frontier_question", payload["by_problem_class"])
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
        self.assertIn("experimental_design_01", by_id)
        self.assertEqual(by_id["experimental_design_01"]["problem_class"], "experimental_design_optimization")
        self.assertTrue(by_id["experimental_design_01"]["evidence_terms"])
        self.assertIn("sequential_change_anytime_01", by_id)
        self.assertEqual(
            by_id["sequential_change_anytime_01"]["problem_class"],
            "sequential_changepoint_inference",
        )
        self.assertTrue(by_id["sequential_change_anytime_01"]["evidence_terms"])
        self.assertIn("geometric_spatial_point_process_02", by_id)
        self.assertEqual(
            by_id["geometric_spatial_point_process_02"]["problem_class"],
            "geometric_spatial_point_process_inference",
        )
        self.assertTrue(by_id["geometric_spatial_point_process_02"]["evidence_terms"])
        self.assertIn("high_dimensional_inference_01", by_id)
        self.assertEqual(
            by_id["high_dimensional_inference_01"]["problem_class"],
            "high_dimensional_latent_structure_inference",
        )
        self.assertTrue(by_id["high_dimensional_inference_01"]["evidence_terms"])
        self.assertIn("statistical_learning_nonparametric_02", by_id)
        self.assertEqual(
            by_id["statistical_learning_nonparametric_02"]["problem_class"],
            "adaptive_transfer_active_preference_learning",
        )
        self.assertTrue(by_id["statistical_learning_nonparametric_02"]["evidence_terms"])
        self.assertIn("robust_privacy_distributed_03", by_id)
        self.assertEqual(
            by_id["robust_privacy_distributed_03"]["problem_class"],
            "robust_distributed_model_privacy_inference",
        )
        self.assertTrue(by_id["robust_privacy_distributed_03"]["evidence_terms"])
        self.assertIn("extremes_tail_heavytail_03", by_id)
        self.assertEqual(
            by_id["extremes_tail_heavytail_03"]["problem_class"],
            "heavy_tail_time_series_extremal_dependence",
        )
        self.assertTrue(by_id["extremes_tail_heavytail_03"]["evidence_terms"])
        self.assertIn("bayesian_computation_posteriors_01", by_id)
        self.assertEqual(
            by_id["bayesian_computation_posteriors_01"]["problem_class"],
            "bayesian_tree_mcmc_computation",
        )
        self.assertTrue(by_id["bayesian_computation_posteriors_01"]["evidence_terms"])
        self.assertIn("bayesian_computation_posteriors_03", by_id)
        self.assertEqual(
            by_id["bayesian_computation_posteriors_03"]["problem_class"],
            "bayesian_tree_mcmc_computation",
        )
        self.assertTrue(by_id["bayesian_computation_posteriors_03"]["evidence_terms"])
        self.assertIn("missing_censored_measurement_error_02", by_id)
        self.assertEqual(
            by_id["missing_censored_measurement_error_02"]["problem_class"],
            "missing_mediation_deconvolution_inference",
        )
        self.assertTrue(by_id["missing_censored_measurement_error_02"]["evidence_terms"])
        self.assertIn("missing_censored_measurement_error_05", by_id)
        self.assertEqual(
            by_id["missing_censored_measurement_error_05"]["problem_class"],
            "missing_mediation_deconvolution_inference",
        )
        self.assertTrue(by_id["missing_censored_measurement_error_05"]["evidence_terms"])
        self.assertIn("networks_graphs_01", by_id)
        self.assertEqual(by_id["networks_graphs_01"]["problem_class"], "network_graph_inference")
        self.assertTrue(by_id["networks_graphs_01"]["evidence_terms"])
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
        self.assertEqual(payload["n_backlog"], 0)
        self.assertEqual(payload["n_ok"], payload["n_backlog"])
        self.assertEqual(payload["n_supported"], 60)
        self.assertEqual(len(payload["by_domain"]), 0)
        self.assertFalse(payload["by_required_primitive"])
        by_id = {row["question_id"]: row for row in payload["rows"]}
        self.assertNotIn("statistical_learning_nonparametric_02", by_id)
        self.assertNotIn("networks_graphs_01", by_id)
        self.assertNotIn("experimental_design_01", by_id)
        self.assertNotIn("sequential_change_anytime_01", by_id)
        self.assertNotIn("geometric_spatial_point_process_02", by_id)
        self.assertNotIn("high_dimensional_inference_01", by_id)
        self.assertNotIn("bayesian_computation_posteriors_05", by_id)
        self.assertNotIn("bayesian_computation_posteriors_01", by_id)
        self.assertNotIn("bayesian_computation_posteriors_03", by_id)
        self.assertNotIn("robust_privacy_distributed_03", by_id)
        self.assertNotIn("extremes_tail_heavytail_03", by_id)
        self.assertNotIn("missing_censored_measurement_error_02", by_id)
        self.assertNotIn("missing_censored_measurement_error_05", by_id)
        for row in payload["rows"]:
            self.assertTrue(row["required_primitives"])
            self.assertTrue(row["likely_methods"])
            self.assertFalse(row["errors"])
        self.assertTrue(Path("runs/test_frontier_backlog_audit/frontier_backlog_manifest.json").exists())
        self.assertTrue(Path("runs/test_frontier_backlog_audit/frontier_backlog.md").exists())

    def test_network_graph_frontier_question_runs_registered_simulator(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "networks_graphs_01"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "network_graph_inference")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual([procedure.algorithm for procedure in procedures], ["sbm_edge_density_spectral"])
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "network_edge_density_unbiasedness",
                "spectral_community_recovery",
                "frontier_network_model_extensions",
            },
        )
        simulations = ResearchSimulator(n_runs=25, seed=20260528).run(problem, procedures)
        self.assertEqual(len(simulations), 1)
        self.assertTrue(simulations[0].passed)
        self.assertEqual(simulations[0].diagnosis.status, "OK")
        self.assertIn("edge_density_rmse", simulations[0].metrics)
        self.assertGreaterEqual(simulations[0].metrics["mean_community_accuracy"], 0.88)

    def test_experimental_design_frontier_question_runs_registered_simulator(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "experimental_design_01"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "experimental_design_optimization")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual([procedure.algorithm for procedure in procedures], ["covariate_balance_maximin_design"])
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "maximin_space_filling_surrogate_validity",
                "covariate_balance_rerandomization_validity",
                "order_addition_stratum_orthogonality",
            },
        )
        simulations = ResearchSimulator(n_runs=25, seed=20260528).run(problem, procedures)
        self.assertEqual(len(simulations), 1)
        self.assertTrue(simulations[0].passed)
        self.assertEqual(simulations[0].diagnosis.status, "OK")
        self.assertGreaterEqual(simulations[0].metrics["space_filling_ratio"], 1.10)
        self.assertGreaterEqual(simulations[0].metrics["balance_improvement"], 1.25)
        self.assertLessEqual(simulations[0].metrics["mean_standardized_imbalance"], 0.35)

    def test_sequential_changepoint_frontier_question_runs_registered_simulator(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "sequential_change_anytime_01"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "sequential_changepoint_inference")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual([procedure.algorithm for procedure in procedures], ["cusum_changepoint_detector"])
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "functional_cusum_changepoint_localization",
                "post_detection_changepoint_confidence_set",
                "sequential_model_confidence_set_validity",
            },
        )
        post_detection_goal = {
            goal.id: goal for goal in theorem_goals
        }["post_detection_changepoint_confidence_set"]
        self.assertIn(
            "selected_bad_event_probability_le_finite_union_budget",
            post_detection_goal.proof_obligations,
        )
        self.assertIn(
            "selected_good_event_coverage_of_finite_union_budget",
            post_detection_goal.proof_obligations,
        )
        simulations = ResearchSimulator(n_runs=25, seed=20260528).run(problem, procedures)
        self.assertEqual(len(simulations), 1)
        self.assertTrue(simulations[0].passed)
        self.assertEqual(simulations[0].diagnosis.status, "OK")
        self.assertGreaterEqual(simulations[0].metrics["detection_rate"], 0.85)
        self.assertLessEqual(simulations[0].metrics["false_alarm_rate"], 0.12)
        self.assertLessEqual(simulations[0].metrics["mean_absolute_localization_error"], 18.0)

    def test_geometric_spatial_frontier_question_runs_registered_simulators(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "geometric_spatial_point_process_02"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "geometric_spatial_point_process_inference")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual(
            [procedure.algorithm for procedure in procedures],
            ["metric_graph_kernel_smoother", "point_process_intensity_contrast"],
        )
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "metric_graph_kernel_prediction_consistency",
                "spde_matern_field_likelihood_validity",
                "point_process_intensity_contrast_validity",
                "superposed_palm_mixture_representation",
            },
        )
        simulations = ResearchSimulator(n_runs=25, seed=20260528).run(problem, procedures)
        self.assertEqual(len(simulations), 2)
        for simulation in simulations:
            self.assertTrue(simulation.passed)
            self.assertEqual(simulation.diagnosis.status, "OK")
        field_sim = next(row for row in simulations if row.procedure_id == "metric_graph_kernel_field_predictor")
        point_sim = next(row for row in simulations if row.procedure_id == "point_process_kernel_intensity_contrast")
        self.assertLessEqual(field_sim.metrics["field_rmse"], 0.22)
        self.assertGreaterEqual(field_sim.metrics["field_coverage_95"], 0.88)
        self.assertLessEqual(abs(point_sim.metrics["intensity_relative_bias"]), 0.10)
        self.assertGreaterEqual(point_sim.metrics["intensity_coverage_95"], 0.88)
        self.assertGreaterEqual(point_sim.metrics["selection_accuracy"], 0.80)

    def test_high_dimensional_latent_frontier_question_runs_registered_simulators(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "high_dimensional_inference_01"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "high_dimensional_latent_structure_inference")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual(
            [procedure.algorithm for procedure in procedures],
            ["latent_simplex_membership", "dimension_association_screening"],
        )
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "latent_simplex_membership_identifiability",
                "sufficient_dimension_association_selection_validity",
                "tensor_multilinear_reduction_consistency",
            },
        )
        simulations = ResearchSimulator(n_runs=35, seed=20260529).run(problem, procedures)
        self.assertEqual(len(simulations), 2)
        for simulation in simulations:
            self.assertTrue(simulation.passed)
            self.assertEqual(simulation.diagnosis.status, "OK")
        membership_sim = next(row for row in simulations if row.procedure_id == "simplex_factor_membership_estimator")
        screening_sim = next(row for row in simulations if row.procedure_id == "nonlinear_dimension_association_screen")
        self.assertLessEqual(membership_sim.metrics["membership_rmse"], 0.25)
        self.assertGreaterEqual(membership_sim.metrics["top_membership_accuracy"], 0.80)
        self.assertGreaterEqual(screening_sim.metrics["active_recall"], 0.80)
        self.assertLessEqual(screening_sim.metrics["false_discovery_rate"], 0.45)
        self.assertGreaterEqual(screening_sim.metrics["subspace_alignment"], 0.70)

    def test_adaptive_transfer_preference_frontier_question_runs_registered_simulators(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "statistical_learning_nonparametric_02"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "adaptive_transfer_active_preference_learning")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual(
            [procedure.algorithm for procedure in procedures],
            ["robust_multitask_gmm_transfer", "contextual_preference_active_labeling"],
        )
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "robust_multitask_gmm_transfer_rate",
                "contextual_preference_online_regret_bound",
                "active_label_efficiency_validity",
            },
        )
        simulations = ResearchSimulator(n_runs=35, seed=20260529).run(problem, procedures)
        self.assertEqual(len(simulations), 2)
        for simulation in simulations:
            self.assertTrue(simulation.passed)
            self.assertEqual(simulation.diagnosis.status, "OK")
        transfer_sim = next(row for row in simulations if row.procedure_id == "robust_multitask_gmm_transfer_estimator")
        preference_sim = next(row for row in simulations if row.procedure_id == "uncertainty_aware_preference_query_policy")
        self.assertGreaterEqual(transfer_sim.metrics["transfer_gain"], 1.25)
        self.assertGreaterEqual(transfer_sim.metrics["outlier_task_detection_accuracy"], 0.85)
        self.assertLessEqual(preference_sim.metrics["mean_regret"], 0.08)
        self.assertGreaterEqual(preference_sim.metrics["best_scheme_selection_accuracy"], 0.82)

    def test_robust_distributed_privacy_frontier_question_runs_registered_simulators(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "robust_privacy_distributed_03"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "robust_distributed_model_privacy_inference")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual(
            [procedure.algorithm for procedure in procedures],
            [
                "robust_proportional_regression",
                "byzantine_distributed_mixture",
                "model_stealing_query_defense",
            ],
        )
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "robust_proportional_regression_validity",
                "byzantine_distributed_mixture_consistency",
                "query_response_model_privacy_bound",
            },
        )
        simulations = ResearchSimulator(n_runs=35, seed=20260529).run(problem, procedures)
        self.assertEqual(len(simulations), 3)
        for simulation in simulations:
            self.assertTrue(simulation.passed)
            self.assertEqual(simulation.diagnosis.status, "OK")
        proportional_sim = next(row for row in simulations if row.procedure_id == "winsorized_proportional_quasi_regression")
        mixture_sim = next(row for row in simulations if row.procedure_id == "label_aligned_byzantine_mixture_aggregator")
        privacy_sim = next(row for row in simulations if row.procedure_id == "noisy_query_model_privacy_defense")
        self.assertLessEqual(proportional_sim.metrics["rmse"], 0.10)
        self.assertGreaterEqual(proportional_sim.metrics["outlier_screening_accuracy"], 0.78)
        self.assertLessEqual(mixture_sim.metrics["rmse"], 0.05)
        self.assertGreaterEqual(mixture_sim.metrics["byzantine_detection_accuracy"], 0.78)
        self.assertGreaterEqual(privacy_sim.metrics["privacy_risk_reduction"], 0.25)
        self.assertGreaterEqual(privacy_sim.metrics["selection_accuracy"], 0.80)

    def test_heavy_tail_time_series_frontier_question_runs_registered_simulators(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "extremes_tail_heavytail_03"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "heavy_tail_time_series_extremal_dependence")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual(
            [procedure.algorithm for procedure in procedures],
            [
                "integrated_acd_infinite_mean_test",
                "hyperplane_extremal_dependence_pca",
                "truncated_factor_time_series",
            ],
        )
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "integrated_acd_infinite_mean_limit",
                "hyperplane_extremal_dependence_representation",
                "tail_robust_factor_time_series_consistency",
            },
        )
        simulations = ResearchSimulator(n_runs=40, seed=20260530).run(problem, procedures)
        self.assertEqual(len(simulations), 3)
        for simulation in simulations:
            self.assertTrue(simulation.passed)
            self.assertEqual(simulation.diagnosis.status, "OK")
        acd_sim = next(row for row in simulations if row.procedure_id == "infinite_mean_acd_tail_index_test")
        hyperplane_sim = next(row for row in simulations if row.procedure_id == "hyperplane_tail_dependence_pca")
        factor_sim = next(row for row in simulations if row.procedure_id == "truncated_tail_factor_subspace")
        self.assertGreaterEqual(acd_sim.metrics["infinite_mean_detection_rate"], 0.85)
        self.assertLessEqual(acd_sim.metrics["tail_alpha_rmse"], 0.12)
        self.assertGreaterEqual(hyperplane_sim.metrics["hyperplane_alignment"], 0.80)
        self.assertGreaterEqual(hyperplane_sim.metrics["selection_accuracy"], 0.85)
        self.assertGreaterEqual(factor_sim.metrics["factor_alignment"], 0.75)
        self.assertLessEqual(factor_sim.metrics["rmse"], 0.38)

    def test_missing_mediation_deconvolution_frontier_question_runs_registered_simulators(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "missing_censored_measurement_error_02"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "missing_mediation_deconvolution_inference")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual(
            [procedure.algorithm for procedure in procedures],
            [
                "shadow_variable_mediation_sieve",
                "platform_adjusted_cell_deconvolution",
            ],
        )
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "shadow_variable_mediation_identification",
                "platform_adjusted_deconvolution_validity",
            },
        )
        simulations = ResearchSimulator(n_runs=45, seed=20260530).run(problem, procedures)
        self.assertEqual(len(simulations), 2)
        for simulation in simulations:
            self.assertTrue(simulation.passed)
            self.assertEqual(simulation.diagnosis.status, "OK")
        mediation_sim = next(row for row in simulations if row.procedure_id == "shadow_variable_mediation_bridge_estimator")
        deconv_sim = next(row for row in simulations if row.procedure_id == "platform_adjusted_cell_type_deconvolution")
        self.assertGreaterEqual(mediation_sim.metrics["shadow_imputation_correlation"], 0.75)
        self.assertLessEqual(mediation_sim.metrics["mediation_indirect_effect_rmse"], 0.06)
        self.assertLessEqual(deconv_sim.metrics["deconvolution_rmse"], 0.075)
        self.assertGreaterEqual(deconv_sim.metrics["dominant_cell_accuracy"], 0.80)
        self.assertLessEqual(deconv_sim.metrics["platform_scale_rmse"], 0.10)

    def test_bayesian_tree_mcmc_frontier_question_runs_registered_simulators(self) -> None:
        question = next(
            row.to_open_research_question()
            for row in load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
            if row.id == "bayesian_computation_posteriors_01"
        )
        problem = ProblemFormalizer().formalize(question)
        self.assertEqual(problem.problem_class, "bayesian_tree_mcmc_computation")
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        self.assertEqual(
            [procedure.algorithm for procedure in procedures],
            [
                "graph_split_bart_surrogate",
                "parallel_metropolis_picard_surrogate",
            ],
        )
        self.assertEqual(
            {goal.id for goal in theorem_goals},
            {
                "graph_split_bart_predictive_consistency",
                "parallel_picard_metropolis_stationarity",
            },
        )
        simulations = ResearchSimulator(n_runs=35, seed=20260531).run(problem, procedures)
        self.assertEqual(len(simulations), 2)
        for simulation in simulations:
            self.assertTrue(simulation.passed)
            self.assertEqual(simulation.diagnosis.status, "OK")
        graph_sim = next(row for row in simulations if row.procedure_id == "graph_split_bart_predictive_surrogate")
        mcmc_sim = next(row for row in simulations if row.procedure_id == "parallel_picard_metropolis_moment_estimator")
        self.assertLessEqual(graph_sim.metrics["rmse"], 0.42)
        self.assertGreaterEqual(graph_sim.metrics["graph_support_recovery"], 0.70)
        self.assertGreaterEqual(graph_sim.metrics["predictive_rmse_gain"], 1.40)
        self.assertGreaterEqual(mcmc_sim.metrics["parallel_speedup"], 1.80)
        self.assertGreaterEqual(mcmc_sim.metrics["acceptance_rate"], 0.15)
        self.assertLessEqual(mcmc_sim.metrics["covariance_rmse"], 0.18)

    def test_frontier_smoke_benchmark_runs_selected_supported_papers(self) -> None:
        out_dir = Path("runs/test_frontier_smoke_benchmark")
        cached_out_dir = Path("runs/test_frontier_smoke_benchmark_cached")
        cache_dir = Path("runs/test_frontier_smoke_cache")
        for path in (out_dir, cached_out_dir, cache_dir):
            shutil.rmtree(path, ignore_errors=True)

        selected, metadata = select_supported_frontier_questions(max_per_class=1)
        self.assertGreaterEqual(len(selected), 3)
        self.assertEqual(len(selected), len(metadata))
        self.assertEqual(len({row.problem_class for row in metadata}), len(metadata))

        all_selected, all_metadata = select_supported_frontier_questions(max_per_class=0)
        all_frontier_rows = load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
        self.assertEqual(len(all_selected), len(all_metadata))
        self.assertEqual(len(all_selected), len(all_frontier_rows))
        self.assertGreater(len(all_selected), len(selected))
        self.assertEqual(len({row.question_id for row in all_metadata}), len(all_metadata))

        async def run(out: Path):
            return await run_frontier_smoke_benchmark(
                out,
                config=FrontierSmokeConfig(n_runs=25, seed=20260528, cache_dir=str(cache_dir)),
                proof_verifier=MockProofVerifier(),
            )

        payload = asyncio.run(run(out_dir))
        self.assertTrue(payload["all_gates_passed"])
        self.assertTrue(payload["gates"]["frontier_theory_target_audit"])
        self.assertEqual(payload["selection_scope"], "per_problem_class_cap")
        self.assertEqual(payload["counts"]["questions"], payload["n_selected"])
        self.assertEqual(payload["counts"]["ready_with_gaps"], payload["n_selected"])
        self.assertEqual(payload["counts"]["traces_ok"], payload["n_selected"])
        self.assertEqual(payload["counts"]["theory_targets_scored"], payload["n_selected"])
        self.assertEqual(payload["counts"]["theory_targets_total"], payload["n_selected"])
        self.assertGreater(payload["counts"]["theory_expected_results"], 0)
        self.assertIn("timings", payload)
        self.assertGreater(payload["timings"]["total_elapsed_ms"], 0)
        self.assertTrue(payload["timings"]["stages"])
        self.assertIn("research_benchmark", {row["stage"] for row in payload["timings"]["stages"]})
        self.assertEqual(payload["counts"]["frontier_smoke_cache_status"], "miss")
        payload_cached = asyncio.run(run(cached_out_dir))
        self.assertTrue(payload_cached["all_gates_passed"])
        self.assertEqual(payload_cached["counts"]["frontier_smoke_cache_status"], "hit")
        self.assertIn(
            "research_benchmark_cache_hit",
            {row["stage"] for row in payload_cached["timings"]["stages"]},
        )
        self.assertEqual(payload["counts"]["frontier_smoke_total_elapsed_ms"], payload["timings"]["total_elapsed_ms"])
        self.assertTrue(payload["counts"]["frontier_smoke_slowest_stage"])
        self.assertTrue((out_dir / "frontier_smoke_manifest.json").exists())
        self.assertTrue((out_dir / "selected_questions.json").exists())
        self.assertTrue(Path(payload["artifacts"]["research_benchmark"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_target_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_evaluation_triage"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_simulation_rerun"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_revision_queue"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_revision_formalization"]).exists())
        self.assertTrue(payload["gates"]["frontier_evaluation_triage"])
        self.assertTrue(payload["gates"]["frontier_simulation_rerun"])
        self.assertTrue(payload["gates"]["frontier_theory_revision_queue"])
        self.assertTrue(payload["gates"]["frontier_theory_revision_formalization"])
        target_audit = json.loads(Path(payload["artifacts"]["frontier_theory_target_audit"]).read_text())
        self.assertTrue(target_audit["all_scored"])
        self.assertFalse(target_audit["limitations"][0] == "")
        triage = json.loads(Path(payload["artifacts"]["frontier_evaluation_triage"]).read_text())
        self.assertTrue(triage["all_ok"])
        self.assertEqual(payload["counts"]["frontier_triage_items"], triage["n_items"])
        rerun = json.loads(Path(payload["artifacts"]["frontier_simulation_rerun"]).read_text())
        self.assertTrue(rerun["all_ok"])
        self.assertEqual(payload["counts"]["frontier_simulation_rerun_items"], rerun["n_items"])
        revision_queue = json.loads(Path(payload["artifacts"]["frontier_theory_revision_queue"]).read_text())
        self.assertTrue(revision_queue["all_ok"])
        self.assertEqual(payload["counts"]["frontier_theory_revision_tasks"], revision_queue["n_tasks"])
        revision_formalization = json.loads(
            Path(payload["artifacts"]["frontier_theory_revision_formalization"]).read_text()
        )
        self.assertTrue(revision_formalization["all_ok"])
        self.assertEqual(
            payload["counts"]["frontier_theory_revision_formal_obligations"],
            revision_formalization["n_obligations"],
        )
        self.assertEqual(
            payload["counts"]["frontier_theory_revision_unique_formal_obligations"],
            revision_formalization["n_unique_obligations"],
        )
        self.assertEqual(
            payload["counts"]["frontier_theory_revision_unique_proof_bank_bridge"]
            + payload["counts"]["frontier_theory_revision_unique_local_source_only"]
            + payload["counts"]["frontier_theory_revision_unique_source_gap"],
            revision_formalization["n_unique_obligations"],
        )
        dp_trace_path = out_dir / "research_benchmark" / "robust_privacy_distributed_02.json"
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
        self.assertIn("finite_family_absolute_error_union_control", measurement_rank_support)
        self.assertIn("simultaneous_coverage_of_union_error_bound", measurement_rank_support)
        self.assertIn("pairwise_top_rank_correct_of_separation", measurement_rank_support)
        self.assertIn("top_rank_correct_of_uniform_error_separation", measurement_rank_support)

    def test_frontier_smoke_benchmark_can_score_all_supported_frontier_entries(self) -> None:
        out_dir = Path("runs/test_frontier_smoke_all_supported")
        shutil.rmtree(out_dir, ignore_errors=True)

        async def run():
            return await run_frontier_smoke_benchmark(
                out_dir,
                config=FrontierSmokeConfig(n_runs=5, seed=20260531, max_per_class=0),
                proof_verifier=MockProofVerifier(),
            )

        payload = asyncio.run(run())
        benchmark_rows = load_frontier_benchmark_questions(Path("docs/frontier_stat_theory_benchmark.md"))
        self.assertIsInstance(payload["all_gates_passed"], bool)
        self.assertEqual(payload["selection_scope"], "all_supported")
        self.assertEqual(payload["n_selected"], len(benchmark_rows))
        self.assertEqual(payload["counts"]["questions"], len(benchmark_rows))
        self.assertEqual(payload["counts"]["traces_total"], len(benchmark_rows))
        self.assertEqual(payload["counts"]["theory_targets_scored"], len(benchmark_rows))
        self.assertEqual(payload["counts"]["theory_targets_total"], len(benchmark_rows))
        self.assertEqual(payload["counts"]["formal_blocked"], 0)
        self.assertEqual(
            payload["counts"]["ready_with_gaps"] + payload["counts"]["simulation_flagged"],
            len(benchmark_rows),
        )
        self.assertGreater(payload["counts"]["theory_expected_results"], 69)
        self.assertGreater(payload["counts"]["theory_expected_results_covered"], 59)
        self.assertGreater(payload["counts"]["theory_expected_result_coverage_rate"], 0.75)
        self.assertEqual(payload["counts"]["frontier_triage_theory_target_misses"], 30)
        self.assertEqual(payload["counts"]["frontier_triage_simulation_flags"], 16)
        self.assertEqual(payload["counts"]["frontier_triage_items"], 46)
        self.assertEqual(payload["counts"]["frontier_simulation_rerun_items"], 16)
        self.assertEqual(payload["counts"]["frontier_simulation_rerun_resolved"], 13)
        self.assertEqual(payload["counts"]["frontier_simulation_rerun_still_flagged"], 3)
        self.assertEqual(payload["counts"]["frontier_theory_revision_tasks"], 3)
        self.assertEqual(payload["counts"]["frontier_theory_revision_tasks_ok"], 3)
        self.assertTrue((out_dir / "frontier_smoke_manifest.json").exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_target_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_evaluation_triage"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_simulation_rerun"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_revision_queue"]).exists())
        self.assertTrue(Path(payload["artifacts"]["frontier_theory_revision_formalization"]).exists())
        target_audit = json.loads(Path(payload["artifacts"]["frontier_theory_target_audit"]).read_text())
        self.assertTrue(target_audit["all_scored"])
        triage = json.loads(Path(payload["artifacts"]["frontier_evaluation_triage"]).read_text())
        self.assertTrue(triage["all_ok"])
        self.assertEqual(triage["n_theory_target_misses"], 30)
        self.assertEqual(triage["n_simulation_flags"], 16)
        self.assertIn("theory_developer", triage["by_owner"])
        self.assertIn("simulator_agent", triage["by_owner"])
        rerun = json.loads(Path(payload["artifacts"]["frontier_simulation_rerun"]).read_text())
        self.assertTrue(rerun["all_ok"])
        self.assertFalse(rerun["all_resolved"])
        self.assertEqual(rerun["n_resolved"], 13)
        self.assertEqual(rerun["n_still_flagged"], 3)
        self.assertEqual(rerun["by_new_owner_agent"]["research_coordinator"], 13)
        self.assertEqual(rerun["by_new_owner_agent"]["theory_developer"], 3)
        revision_queue = json.loads(Path(payload["artifacts"]["frontier_theory_revision_queue"]).read_text())
        self.assertTrue(revision_queue["all_ok"])
        self.assertEqual(revision_queue["n_tasks"], 3)
        self.assertEqual(revision_queue["by_failure_class"]["selection_or_screening_failure"], 3)
        first_revision = revision_queue["rows"][0]
        self.assertIn("screening_selection_accuracy_under_signal_separation", first_revision["revised_theorem_goals"])
        self.assertIn("selection_accuracy_lower_bound_from_support_events", first_revision["next_formal_obligations"])
        revision_formalization = json.loads(
            Path(payload["artifacts"]["frontier_theory_revision_formalization"]).read_text()
        )
        self.assertTrue(revision_formalization["all_ok"])
        self.assertEqual(revision_formalization["n_revision_tasks"], 3)
        self.assertEqual(revision_formalization["n_obligations"], 12)
        self.assertEqual(revision_formalization["n_unique_obligations"], 4)
        self.assertEqual(revision_formalization["n_unique_proof_bank_bridge"], 4)
        self.assertEqual(revision_formalization["n_unique_local_source_only"], 0)
        self.assertEqual(revision_formalization["n_unique_source_gap"], 0)
        self.assertEqual(payload["counts"]["frontier_theory_revision_formal_obligations"], 12)
        self.assertEqual(payload["counts"]["frontier_theory_revision_unique_formal_obligations"], 4)
        self.assertEqual(payload["counts"]["frontier_theory_revision_unique_proof_bank_bridge"], 4)
        self.assertEqual(payload["counts"]["frontier_theory_revision_unique_local_source_only"], 0)
        self.assertEqual(payload["counts"]["frontier_theory_revision_unique_source_gap"], 0)
        self.assertEqual(
            revision_formalization["n_unique_proof_bank_bridge"]
            + revision_formalization["n_unique_local_source_only"]
            + revision_formalization["n_unique_source_gap"],
            4,
        )
        self.assertEqual(
            {row["formal_obligation"] for row in revision_formalization["rows"]},
            {
                "screening_statistic_concentration",
                "signal_margin_implies_active_selection",
                "inactive_coordinate_union_bound",
                "selection_accuracy_lower_bound_from_support_events",
            },
        )
        high_dim_trace = json.loads(
            (out_dir / "research_benchmark" / "high_dimensional_inference_01.json").read_text()
        )
        high_dim_goals = {row["id"]: row for row in high_dim_trace["theorem_goals"]}
        screening_support = high_dim_goals["sufficient_dimension_association_selection_validity"][
            "proof_obligations"
        ]
        for obligation_id in (
            "screening_statistic_concentration",
            "signal_margin_implies_active_selection",
            "inactive_coordinate_union_bound",
            "selection_accuracy_lower_bound_from_support_events",
        ):
            self.assertIn(obligation_id, screening_support)
        high_dim_proved = {
            row["proof_obligation_id"]
            for row in high_dim_trace["formal_subclaims"]
            if row["status"] == "PROVED"
        }
        self.assertTrue(set(screening_support) <= high_dim_proved)

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

    def test_capability_eval_suite_ladder_records_current_release_evidence(self) -> None:
        path = Path("benchmarks/capability_eval_suites.json")
        self.assertTrue(path.exists())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        evidence = payload["current_release_evidence"]
        proof_bank_size = len(all_obligations())
        self.assertEqual(
            evidence["proof_bank_kernel_verified_release"],
            f"{proof_bank_size}/{proof_bank_size}",
        )
        self.assertEqual(len(evidence["proof_bank_fingerprint"]), 64)
        self.assertEqual(evidence["frontier_supported"], "60/60")
        self.assertEqual(evidence["missing_formal_primitives"], 97)
        self.assertEqual(evidence["formalization_targets_with_proof_bank_bridge"], 74)
        self.assertEqual(evidence["formalization_targets_local_source_only"], 23)
        self.assertEqual(evidence["proof_bank_expansion_bridge_ready"], 60)

        suites = {row["id"]: row for row in payload["suites"]}
        self.assertEqual(set(suites), {f"S{i}_{suffix}" for i, suffix in (
            (0, "release_sanity"),
            (1, "core_method_e2e"),
            (2, "frontier_static_coverage"),
            (3, "frontier_blind_theory_target"),
            (4, "formal_primitive_ladder"),
            (5, "proof_bank_and_search"),
            (6, "algorithm_simulation_stress"),
            (7, "feedback_loop_repair"),
            (8, "adversarial_unsupported_intake"),
            (9, "fresh_holdout_frontier"),
        )})
        self.assertEqual(suites["S4_formal_primitive_ladder"]["current_bridge_ready"], 60)
        self.assertEqual(suites["S4_formal_primitive_ladder"]["current_local_source_only"], 23)
        self.assertEqual(suites["S5_proof_bank_and_search"]["current_proof_bank_size"], proof_bank_size)
        self.assertEqual(suites["S3_frontier_blind_theory_target"]["current_all_supported_size"], 60)
        self.assertEqual(
            suites["S3_frontier_blind_theory_target"]["current_all_supported_expected_results"],
            180,
        )
        self.assertEqual(
            suites["S3_frontier_blind_theory_target"]["current_all_supported_expected_results_covered"],
            149,
        )
        self.assertEqual(suites["S3_frontier_blind_theory_target"]["current_all_supported_simulation_flagged"], 16)
        self.assertEqual(suites["S3_frontier_blind_theory_target"]["current_all_supported_triage_items"], 46)
        self.assertEqual(
            suites["S3_frontier_blind_theory_target"]["current_all_supported_triage_theory_target_misses"],
            30,
        )
        self.assertEqual(
            suites["S3_frontier_blind_theory_target"]["current_all_supported_simulation_rerun_resolved"],
            13,
        )
        self.assertEqual(
            suites["S3_frontier_blind_theory_target"]["current_all_supported_simulation_rerun_still_flagged"],
            3,
        )
        self.assertEqual(
            suites["S3_frontier_blind_theory_target"]["current_all_supported_theory_revision_tasks"],
            3,
        )
        self.assertIn("S7_feedback_loop_repair_with_seeded_failures", payload["recommended_next_gate_stack"])

        doc = Path("docs/evaluation_benchmark_strategy.md").read_text(encoding="utf-8")
        self.assertIn("`proofs_kernel_verified=93/93`", doc)
        self.assertIn("expected-result coverage about 82.8%", doc)
        self.assertIn("46 frontier-evaluation triage items", doc)
        self.assertIn("resolves 13/16 simulation flags", doc)
        self.assertIn("3 unresolved reruns now export scoped TheoryDeveloper revision tasks", doc)
        self.assertIn("60 have ranked proof-bank bridge candidates", doc)
        self.assertNotIn("79/79", doc)
        self.assertNotIn("82/82", doc)

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
        self.assertEqual(payload["formal_source_search"]["backend"], "sqlite_fts_shape_graph_hybrid")
        self.assertEqual(payload["formal_source_search"]["graph_backend"], "declaration_symbol_graph")
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
        causal_goals = {row["id"]: row for row in trace_payload["theorem_goals"]}
        self.assertIn(
            "independent_real_condExp_natural_eq_mean",
            causal_goals["aipw_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "iid_real_clt_tendsto_distribution",
            causal_goals["aipw_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "slutsky_add_negligible_zero_real",
            causal_goals["aipw_asymptotic_normality"]["proof_obligations"],
        )
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
            [
                "difference_estimator_unbiased",
                "aipw_score_expectation_decompose",
                "propensity_weight_mul_cancel_of_lower_bound",
                "propensity_weight_cancel_left_of_lower_bound",
                "aipw_score_expectation_target_of_aug_cancel",
                "integrable_l1_tendsto_condexp_filtration",
                "integrable_ae_tendsto_condexp_filtration",
                "condexp_integral_eq_integral_real",
                "conditional_mean_residual_zero_of_condExp_ae_eq",
                "conditional_mean_residual_zero_of_mean_eq",
                "aipw_score_expectation_target_of_zero_aug",
                "aipw_score_integrable_of_components",
            ],
        )
        conformal_trace = json.loads(Path("runs/test_research_benchmark/conformal_prediction_coverage.json").read_text())
        conformal_goals = {row["id"]: row for row in conformal_trace["theorem_goals"]}
        self.assertIn(
            "coverage_lower_bound_of_complement_error",
            conformal_goals["split_conformal_finite_sample_coverage"]["proof_obligations"],
        )
        self.assertIn(
            "simultaneous_coverage_of_union_error_bound",
            conformal_goals["split_conformal_finite_sample_coverage"]["proof_obligations"],
        )
        hetero_trace = json.loads(Path("runs/test_research_benchmark/heteroskedastic_regression_hc.json").read_text())
        hetero_goals = {row["id"]: row for row in hetero_trace["theorem_goals"]}
        self.assertIn(
            "independent_real_condExp_natural_eq_mean",
            hetero_goals["ols_consistency"]["proof_obligations"],
        )
        self.assertIn(
            "coverage_lower_bound_of_complement_error",
            hetero_goals["hc1_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "iid_real_clt_tendsto_distribution",
            hetero_goals["hc1_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "tendsto_in_distribution_continuous_mapping",
            hetero_goals["hc1_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "slutsky_add_negligible_zero_real",
            hetero_goals["hc1_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "wald_interval_miscoverage_iff_abs_error_gt",
            hetero_goals["hc1_asymptotic_normality"]["proof_obligations"],
        )
        survival_trace = json.loads(Path("runs/test_research_benchmark/right_censored_survival_km.json").read_text())
        survival_goals = {row["id"]: row for row in survival_trace["theorem_goals"]}
        self.assertIn(
            "martingale_ae_eq_condexp_limit_process",
            survival_goals["kaplan_meier_fixed_time_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "submartingale_l1_tendsto_limit_process",
            survival_goals["kaplan_meier_fixed_time_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "submartingale_ae_tendsto_limit_process",
            survival_goals["kaplan_meier_fixed_time_asymptotic_normality"]["proof_obligations"],
        )
        self.assertIn(
            "submartingale_expected_stopped_value_mono",
            survival_goals["kaplan_meier_fixed_time_asymptotic_normality"]["proof_obligations"],
        )
        sequential_trace = json.loads(Path("runs/test_research_benchmark/sequential_anytime_bernoulli.json").read_text())
        sequential_goals = {row["id"]: row for row in sequential_trace["theorem_goals"]}
        self.assertIn(
            "submartingale_doob_maximal_ineq",
            sequential_goals["eprocess_optional_stopping_control"]["proof_obligations"],
        )
        self.assertIn(
            "submartingale_doob_maximal_budget",
            sequential_goals["eprocess_optional_stopping_control"]["proof_obligations"],
        )
        self.assertIn(
            "supermartingale_expected_stopped_value_antimono",
            sequential_goals["eprocess_optional_stopping_control"]["proof_obligations"],
        )
        self.assertIn(
            "submartingale_doob_maximal_probability_bound",
            sequential_goals["eprocess_optional_stopping_control"]["proof_obligations"],
        )
        self.assertIn(
            "event_indicator_product_integral_eq_inter",
            sequential_goals["bernoulli_lr_eprocess_martingale"]["proof_obligations"],
        )
        self.assertIn(
            "independent_event_indicator_product_lintegral_eq_mul",
            sequential_goals["bernoulli_lr_eprocess_martingale"]["proof_obligations"],
        )
        self.assertIn(
            "independent_event_indicator_condExp_filtration_eq_prob",
            sequential_goals["bernoulli_lr_eprocess_martingale"]["proof_obligations"],
        )
        self.assertIn(
            "independent_real_condExp_natural_eq_mean",
            sequential_goals["bernoulli_lr_eprocess_martingale"]["proof_obligations"],
        )
        fdr_trace = json.loads(Path("runs/test_research_benchmark/multiple_testing_fdr_bh.json").read_text())
        fdr_goals = {row["id"]: row for row in fdr_trace["theorem_goals"]}
        self.assertIn(
            "finite_null_family_no_false_rejection_probability",
            fdr_goals["bh_fdr_control_independence"]["proof_obligations"],
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
        self.assertEqual(payload["n_questions"], 11)
        self.assertEqual(payload["n_ready_with_gaps"], 11)
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
                "structural_break_functional_ts",
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
                "sequential_changepoint_inference",
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
        self.assertGreater(payload["n_theorem_goal_proof_obligations"], 0)
        self.assertEqual(
            payload["n_verified_theorem_goal_proof_obligations"],
            payload["n_theorem_goal_proof_obligations"],
        )
        self.assertGreater(payload["n_unique_theorem_goal_proof_obligations"], 0)
        self.assertEqual(
            payload["n_unique_verified_theorem_goal_proof_obligations"],
            payload["n_unique_theorem_goal_proof_obligations"],
        )
        self.assertEqual(payload["theorem_goal_proof_obligation_coverage_rate"], 1.0)
        self.assertTrue(
            any(row["n_theorem_goal_proof_obligations"] > 0 for row in payload["rows"])
        )
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

    def test_formalization_target_audit_maps_post_selection_primitives_to_verified_bridges(self) -> None:
        run_dir = Path("runs/test_formalization_target_post_selection_run")
        out_dir = Path("runs/test_formalization_target_post_selection_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        post_gap_path = gap_dir / "post_detection_changepoint_confidence_set.lean"
        model_gap_path = gap_dir / "sequential_model_confidence_set_validity.lean"
        post_gap_path.write_text(
            "FORMAL_GAP post_selection_inference selected_interval_coverage changepoint_stopping_rule "
            "bootstrap_validity_for_dependent_data",
            encoding="utf-8",
        )
        model_gap_path.write_text(
            "FORMAL_GAP model_confidence_set_coverage sequential_elimination_rule "
            "candidate_model_loss_process dependent_performance_process_bootstrap",
            encoding="utf-8",
        )
        manifest = {
            "questions": [
                {"question": "q_post_selection", "formal": {"gaps": 2}},
            ],
        }
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        proved = [
            {"status": "PROVED", "proof_obligation_id": obligation_id}
            for obligation_id in (
                "prob_compl",
                "coverage_lower_bound_of_complement_error",
                "event_probability_mono",
                "finite_union_bound",
                "selected_bad_event_probability_le_finite_union_budget",
                "selected_good_event_coverage_of_finite_union_budget",
                "prob_measure_univ",
                "simultaneous_coverage_of_union_error_bound",
            )
        ]
        trace = {
            "question": {"id": "q_post_selection"},
            "problem": {"problem_class": "sequential_changepoint_inference"},
            "procedures": [],
            "knowledge": [{"id": "sequential_changepoint_post_detection"}],
            "theorem_goals": [
                {
                    "id": "post_detection_changepoint_confidence_set",
                    "title": "Post-detection changepoint confidence set validity",
                    "proof_strategy": "Bridge detector error control to selected-interval coverage.",
                    "required_primitives": [
                        "changepoint_stopping_rule",
                        "post_selection_inference",
                        "selected_interval_coverage",
                        "bootstrap_validity_for_dependent_data",
                    ],
                    "proof_obligations": [
                        "prob_compl",
                        "coverage_lower_bound_of_complement_error",
                        "event_probability_mono",
                        "finite_union_bound",
                        "selected_bad_event_probability_le_finite_union_budget",
                        "selected_good_event_coverage_of_finite_union_budget",
                    ],
                },
                {
                    "id": "sequential_model_confidence_set_validity",
                    "title": "Sequential model confidence set validity",
                    "proof_strategy": "Reduce model-confidence coverage to finite-time union control.",
                    "required_primitives": [
                        "candidate_model_loss_process",
                        "sequential_elimination_rule",
                        "model_confidence_set_coverage",
                        "dependent_performance_process_bootstrap",
                    ],
                    "proof_obligations": [
                        "prob_measure_univ",
                        "finite_union_bound",
                        "simultaneous_coverage_of_union_error_bound",
                    ],
                },
            ],
            "formal_subclaims": [
                *proved,
                {
                    "id": "gap:post_detection_changepoint_confidence_set",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "selective inference primitives remain library work",
                    "artifact_path": str(post_gap_path),
                    "lean_statement": post_gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "StatInference.AsymptoticStatistics.vaart1998_confidenceIntervalCoverageEvent_efron"}],
                    "primitive_formal_source_hits": {
                        primitive: [
                            {"name": "StatInference.AsymptoticStatistics.vaart1998_confidenceIntervalCoverageEvent_efron"}
                        ]
                        for primitive in (
                            "changepoint_stopping_rule",
                            "post_selection_inference",
                            "selected_interval_coverage",
                            "bootstrap_validity_for_dependent_data",
                        )
                    },
                },
                {
                    "id": "gap:sequential_model_confidence_set_validity",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "model-confidence selective coverage primitives remain library work",
                    "artifact_path": str(model_gap_path),
                    "lean_statement": model_gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "StatInference.FiniteUnionDeviationCertificate.toEmpiricalDeviationBoundOn"}],
                    "primitive_formal_source_hits": {
                        primitive: [
                            {"name": "StatInference.FiniteUnionDeviationCertificate.toEmpiricalDeviationBoundOn"}
                        ]
                        for primitive in (
                            "candidate_model_loss_process",
                            "sequential_elimination_rule",
                            "model_confidence_set_coverage",
                            "dependent_performance_process_bootstrap",
                        )
                    },
                },
            ],
        }
        (run_dir / "q_post_selection.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        self.assertIn(
            "selected_bad_event_probability_le_finite_union_budget",
            rows["post_selection_inference"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "selected_good_event_coverage_of_finite_union_budget",
            rows["post_selection_inference"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "selected_good_event_coverage_of_finite_union_budget",
            rows["selected_interval_coverage"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "selected_good_event_coverage_of_finite_union_budget",
            rows["model_confidence_set_coverage"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "sequential_elimination_rule_finite_union_control",
            rows["sequential_elimination_rule"]["bridge_candidate_obligations"],
        )
        self.assertEqual(rows["post_selection_inference"]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertEqual(rows["model_confidence_set_coverage"]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertEqual(rows["sequential_elimination_rule"]["priority_band"], "BRIDGE_REUSE_READY")

    def test_formalization_target_audit_maps_conformal_counting_primitives_to_verified_bridge(self) -> None:
        run_dir = Path("runs/test_formalization_target_conformal_run")
        out_dir = Path("runs/test_formalization_target_conformal_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        gap_path = gap_dir / "split_conformal_finite_sample_coverage.lean"
        primitives = (
            "exchangeable_scores",
            "rank_uniformity",
            "order_statistic_quantile_rule",
            "finite_sample_coverage_counting",
        )
        gap_path.write_text("FORMAL_GAP " + " ".join(primitives), encoding="utf-8")
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps({"questions": [{"question": "q_conformal", "formal": {"gaps": 1}}]}),
            encoding="utf-8",
        )
        proof_obligations = (
            "prob_measure_univ",
            "prob_compl",
            "coverage_lower_bound_of_complement_error",
            "event_probability_mono",
            "finite_union_bound",
            "finite_union_budget_control",
            "simultaneous_coverage_of_union_error_bound",
            "finite_conformal_rank_coverage_counting",
        )
        trace = {
            "question": {"id": "q_conformal"},
            "problem": {"problem_class": "distribution_free_conformal_prediction"},
            "procedures": [],
            "knowledge": [{"id": "split_conformal_prediction"}],
            "theorem_goals": [
                {
                    "id": "split_conformal_finite_sample_coverage",
                    "title": "Split conformal finite-sample coverage",
                    "proof_strategy": "Formalize ranks of exchangeable nonconformity scores and order-statistic quantile rule.",
                    "required_primitives": list(primitives),
                    "proof_obligations": list(proof_obligations),
                },
            ],
            "formal_subclaims": [
                *[
                    {"status": "PROVED", "proof_obligation_id": obligation_id}
                    for obligation_id in proof_obligations
                ],
                {
                    "id": "gap:split_conformal_finite_sample_coverage",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "exchangeability and order-statistic rank theorem remain library work",
                    "artifact_path": str(gap_path),
                    "lean_statement": gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "StatInference.VdVWInnerProbability_add_outerMeasure_compl"}],
                    "primitive_formal_source_hits": {
                        primitive: [{"name": "StatInference.VdVWInnerProbability_add_outerMeasure_compl"}]
                        for primitive in primitives
                    },
                },
            ],
        }
        (run_dir / "q_conformal.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        self.assertIn(
            "uniform_rank_pmf_mass",
            rows["exchangeable_scores"]["bridge_candidate_obligations"],
        )
        self.assertEqual(rows["exchangeable_scores"]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertIn(
            "uniform_rank_pmf_mass",
            rows["rank_uniformity"]["bridge_candidate_obligations"],
        )
        for primitive in (
            "finite_sample_coverage_counting",
            "rank_uniformity",
            "order_statistic_quantile_rule",
        ):
            self.assertIn(
                "finite_conformal_rank_coverage_counting",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertEqual(rows[primitive]["priority_band"], "BRIDGE_REUSE_READY")

    def test_formalization_target_audit_maps_multiple_testing_pvalue_primitives_to_verified_bridge(self) -> None:
        run_dir = Path("runs/test_formalization_target_pvalue_run")
        out_dir = Path("runs/test_formalization_target_pvalue_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        gap_path = gap_dir / "bh_fdr_control_independence.lean"
        primitives = (
            "valid_null_pvalue_uniformity",
            "ordered_pvalues",
            "bh_stepup_self_consistency",
            "bh_threshold_fixed_point",
            "leave_one_out_fdr_decomposition",
            "independent_null_pvalues",
        )
        gap_path.write_text("FORMAL_GAP " + " ".join(primitives), encoding="utf-8")
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps({"questions": [{"question": "q_pvalues", "formal": {"gaps": 1}}]}),
            encoding="utf-8",
        )
        proof_obligations = (
            "prob_measure_univ",
            "prob_compl",
            "event_probability_mono",
            "independent_event_inter_probability",
            "independent_null_event_family_inter_probability",
            "independent_null_event_family_compl_inter_probability",
            "finite_union_bound",
            "finite_union_budget_control",
            "finite_null_family_no_false_rejection_probability",
            "finite_null_pvalue_no_false_rejection_probability",
            "markov_inequality",
        )
        trace = {
            "question": {"id": "q_pvalues"},
            "problem": {"problem_class": "multiple_testing_fdr"},
            "procedures": [],
            "knowledge": [{"id": "multiple_testing_bh"}],
            "theorem_goals": [
                {
                    "id": "bh_fdr_control_independence",
                    "title": "Benjamini-Hochberg FDR control under independent null p-values",
                    "proof_strategy": "Formalize ordered p-values, self-consistency, and leave-one-out decomposition.",
                    "required_primitives": list(primitives),
                    "proof_obligations": list(proof_obligations),
                },
            ],
            "formal_subclaims": [
                *[
                    {"status": "PROVED", "proof_obligation_id": obligation_id}
                    for obligation_id in proof_obligations
                ],
                {
                    "id": "gap:bh_fdr_control_independence",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "BH step-up FDR proof remains theorem-library work",
                    "artifact_path": str(gap_path),
                    "lean_statement": gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "StatInference.FiniteUnionDeviationCertificate.toEmpiricalDeviationBoundOn"}],
                    "primitive_formal_source_hits": {
                        primitive: [{"name": "StatInference.FiniteUnionDeviationCertificate.toEmpiricalDeviationBoundOn"}]
                        for primitive in primitives
                    },
                },
            ],
        }
        (run_dir / "q_pvalues.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        for primitive in (
            "valid_null_pvalue_uniformity",
            "ordered_pvalues",
            "bh_stepup_self_consistency",
            "leave_one_out_fdr_decomposition",
        ):
            self.assertIn(
                "finite_null_pvalue_no_false_rejection_probability",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertEqual(rows[primitive]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertIn("bh_threshold_grid_mono", rows["ordered_pvalues"]["bridge_candidate_obligations"])
        self.assertIn(
            "bh_threshold_grid_mono",
            rows["bh_stepup_self_consistency"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "bh_threshold_grid_mono",
            rows["bh_threshold_fixed_point"]["bridge_candidate_obligations"],
        )
        self.assertEqual(rows["bh_threshold_fixed_point"]["priority_band"], "BRIDGE_REUSE_READY")

    def test_formalization_target_audit_maps_causal_consistency_primitive_to_verified_bridge(self) -> None:
        run_dir = Path("runs/test_formalization_target_causal_run")
        out_dir = Path("runs/test_formalization_target_causal_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        gap_path = gap_dir / "aipw_identification.lean"
        primitives = (
            "potential_outcome_consistency",
            "conditional_exchangeability",
            "positivity",
            "propensity_weight_identity",
        )
        gap_path.write_text("FORMAL_GAP " + " ".join(primitives), encoding="utf-8")
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps({"questions": [{"question": "q_causal", "formal": {"gaps": 1}}]}),
            encoding="utf-8",
        )
        proof_obligations = (
            "event_indicator_expectation",
            "prob_measure_univ",
            "integral_of_constant",
            "potential_outcome_observed_consistency",
            "condexp_integral_eq_integral_real",
            "aipw_score_expectation_decompose",
            "propensity_weight_mul_cancel_of_lower_bound",
            "propensity_weight_cancel_left_of_lower_bound",
            "aipw_score_expectation_target_of_aug_cancel",
            "conditional_mean_residual_zero_of_condExp_ae_eq",
            "conditional_mean_residual_zero_of_mean_eq",
            "aipw_score_expectation_target_of_zero_aug",
            "aipw_score_integrable_of_components",
        )
        trace = {
            "question": {"id": "q_causal"},
            "problem": {"problem_class": "semiparametric_causal_ate"},
            "procedures": [],
            "knowledge": [{"id": "aipw_double_robustness"}],
            "theorem_goals": [
                {
                    "id": "aipw_identification",
                    "title": "ATE identification by consistency, exchangeability, and positivity",
                    "proof_strategy": "Formalize potential-outcome consistency first, then conditional exchangeability and positivity.",
                    "required_primitives": list(primitives),
                    "proof_obligations": list(proof_obligations),
                },
            ],
            "formal_subclaims": [
                *[
                    {"status": "PROVED", "proof_obligation_id": obligation_id}
                    for obligation_id in proof_obligations
                ],
                {
                    "id": "gap:aipw_identification",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "conditional exchangeability and positivity remain library work",
                    "artifact_path": str(gap_path),
                    "lean_statement": gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "StatInference.DeterministicATECase.ateEstimand"}],
                    "primitive_formal_source_hits": {
                        primitive: [{"name": "StatInference.DeterministicATECase.ateEstimand"}]
                        for primitive in primitives
                    },
                },
            ],
        }
        (run_dir / "q_causal.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        self.assertIn(
            "potential_outcome_observed_consistency",
            rows["potential_outcome_consistency"]["bridge_candidate_obligations"],
        )
        self.assertEqual(rows["potential_outcome_consistency"]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertIn(
            "propensity_score_ne_zero_of_lower_bound",
            rows["positivity"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "propensity_weight_mul_cancel_of_lower_bound",
            rows["positivity"]["bridge_candidate_obligations"],
        )
        self.assertEqual(rows["positivity"]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertIn(
            "propensity_weight_mul_cancel_of_lower_bound",
            rows["propensity_weight_identity"]["bridge_candidate_obligations"],
        )
        self.assertEqual(rows["propensity_weight_identity"]["priority_band"], "BRIDGE_REUSE_READY")

    def test_formalization_target_audit_maps_design_based_primitives_to_verified_bridge(self) -> None:
        run_dir = Path("runs/test_formalization_target_design_based_run")
        out_dir = Path("runs/test_formalization_target_design_based_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        gap_path = gap_dir / "neyman_variance_conservative_validity.lean"
        primitives = (
            "finite_population_potential_outcomes",
            "complete_randomization_distribution",
            "difference_in_means_unbiasedness",
            "randomization_variance_decomposition",
            "neyman_bound_nonnegative_treatment_effect_variance",
        )
        gap_path.write_text("FORMAL_GAP " + " ".join(primitives), encoding="utf-8")
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps({"questions": [{"question": "q_design", "formal": {"gaps": 1}}]}),
            encoding="utf-8",
        )
        proof_obligations = (
            "finite_population_ate_mean_difference",
            "complete_randomization_uniform_assignment_mass",
            "finite_sample_mean_unbiased",
            "difference_estimator_unbiased",
            "difference_estimator_variance_decompose",
            "neyman_variance_conservative_algebra",
            "mean2_estimator_unbiased",
            "mean2_estimator_variance_indep",
            "finite_sample_mean_variance_indep",
            "finite_sample_mean_chebyshev_indep",
            "estimator_error_chebyshev",
            "variance_nonneg",
        )
        trace = {
            "question": {"id": "q_design"},
            "problem": {"problem_class": "design_based_variance_inference"},
            "procedures": [],
            "knowledge": [{"id": "design_based_neyman_variance"}],
            "theorem_goals": [
                {
                    "id": "neyman_variance_conservative_validity",
                    "title": "Neyman variance estimator is conservative for finite-population ATE",
                    "proof_strategy": "Bridge difference-in-means expectation and variance algebra to the conservative Neyman bound.",
                    "required_primitives": list(primitives),
                    "proof_obligations": list(proof_obligations),
                },
            ],
            "formal_subclaims": [
                *[
                    {"status": "PROVED", "proof_obligation_id": obligation_id}
                    for obligation_id in proof_obligations
                ],
                {
                    "id": "gap:neyman_variance_conservative_validity",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "complete randomization and finite-population variance derivation remain library work",
                    "artifact_path": str(gap_path),
                    "lean_statement": gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "StatInference.AsymptoticStatistics.experiment_variance"}],
                    "primitive_formal_source_hits": {
                        primitive: [{"name": "StatInference.AsymptoticStatistics.experiment_variance"}]
                        for primitive in primitives
                    },
                },
            ],
        }
        (run_dir / "q_design.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        self.assertIn(
            "finite_population_ate_mean_difference",
            rows["finite_population_potential_outcomes"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "complete_randomization_uniform_assignment_mass",
            rows["complete_randomization_distribution"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "difference_estimator_unbiased",
            rows["difference_in_means_unbiasedness"]["bridge_candidate_obligations"],
        )
        for primitive in (
            "randomization_variance_decomposition",
            "neyman_bound_nonnegative_treatment_effect_variance",
        ):
            self.assertIn(
                "neyman_variance_conservative_algebra",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertEqual(rows[primitive]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertNotIn(
            "neyman_variance_conservative_algebra",
            rows["complete_randomization_distribution"]["bridge_candidate_obligations"],
        )

    def test_formalization_target_audit_maps_robust_mean_primitives_to_verified_bridge(self) -> None:
        run_dir = Path("runs/test_formalization_target_robust_mean_run")
        out_dir = Path("runs/test_formalization_target_robust_mean_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        gap_path = gap_dir / "median_of_means_subgaussian_deviation.lean"
        primitives = (
            "block_mean_definition",
            "chebyshev_block_failure_bound",
            "independent_blocks",
            "median_of_means_deviation",
            "binomial_median_tail_bound",
        )
        gap_path.write_text("FORMAL_GAP " + " ".join(primitives), encoding="utf-8")
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps({"questions": [{"question": "q_robust_mean", "formal": {"gaps": 1}}]}),
            encoding="utf-8",
        )
        proof_obligations = (
            "finite_sample_mean_unbiased",
            "finite_sample_mean_variance_indep",
            "finite_sample_mean_chebyshev_indep",
            "block_estimator_chebyshev_bound",
            "median_of_means_failure_union_control",
            "estimator_error_chebyshev",
            "markov_inequality",
        )
        trace = {
            "question": {"id": "q_robust_mean"},
            "problem": {"problem_class": "robust_mean_inference"},
            "procedures": [],
            "knowledge": [{"id": "robust_mean_median_of_means"}],
            "theorem_goals": [
                {
                    "id": "median_of_means_subgaussian_deviation",
                    "title": "Median-of-means robust sub-Gaussian deviation bound",
                    "proof_strategy": "Bridge block-level Chebyshev failures to finite-block MoM failure control.",
                    "required_primitives": list(primitives),
                    "proof_obligations": list(proof_obligations),
                },
            ],
            "formal_subclaims": [
                *[
                    {"status": "PROVED", "proof_obligation_id": obligation_id}
                    for obligation_id in proof_obligations
                ],
                {
                    "id": "gap:median_of_means_subgaussian_deviation",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "binomial median amplification remains library work",
                    "artifact_path": str(gap_path),
                    "lean_statement": gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "StatInference.FiniteUnionDeviationCertificate.toEmpiricalDeviationBoundOn"}],
                    "primitive_formal_source_hits": {
                        primitive: [{"name": "StatInference.FiniteUnionDeviationCertificate.toEmpiricalDeviationBoundOn"}]
                        for primitive in primitives
                    },
                },
            ],
        }
        (run_dir / "q_robust_mean.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        for primitive in (
            "block_mean_definition",
            "chebyshev_block_failure_bound",
            "independent_blocks",
            "median_of_means_deviation",
        ):
            self.assertIn(
                "median_of_means_failure_union_control",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertEqual(rows[primitive]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertIn("binomial_median_tail_bound", rows)
        self.assertNotIn(
            "median_of_means_failure_union_control",
            rows["binomial_median_tail_bound"]["bridge_candidate_obligations"],
        )

    def test_formalization_target_audit_maps_product_process_primitives_to_indicator_product_bridge(self) -> None:
        run_dir = Path("runs/test_formalization_target_product_process_run")
        out_dir = Path("runs/test_formalization_target_product_process_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        gap_path = gap_dir / "bernoulli_lr_eprocess_martingale.lean"
        primitives = (
            "bernoulli_likelihood_ratio",
            "adapted_product_process",
            "conditional_expectation_product_step",
            "independent_bernoulli_sequence",
            "martingale_definition",
        )
        gap_path.write_text("FORMAL_GAP " + " ".join(primitives), encoding="utf-8")
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps({"questions": [{"question": "q_seq", "formal": {"gaps": 1}}]}),
            encoding="utf-8",
        )
        proof_obligations = (
            "event_indicator_expectation",
            "event_indicator_product_integral_eq_inter",
            "independent_event_indicator_product_lintegral_eq_mul",
            "independent_event_indicator_condExp_filtration_eq_prob",
            "finite_event_indicator_mean_unbiased",
            "independent_event_inter_probability",
        )
        trace = {
            "question": {"id": "q_seq"},
            "problem": {"problem_class": "sequential_anytime_inference"},
            "procedures": [],
            "knowledge": [{"id": "eprocess_anytime_testing"}],
            "theorem_goals": [
                {
                    "id": "bernoulli_lr_eprocess_martingale",
                    "title": "Bernoulli likelihood-ratio process is a null martingale",
                    "proof_strategy": "Use event-indicator product integrals and independence before martingale lifting.",
                    "required_primitives": list(primitives),
                    "proof_obligations": list(proof_obligations),
                },
            ],
            "formal_subclaims": [
                *[
                    {"status": "PROVED", "proof_obligation_id": obligation_id}
                    for obligation_id in proof_obligations
                ],
                {
                    "id": "gap:bernoulli_lr_eprocess_martingale",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "martingale conditional-expectation lifting remains library work",
                    "artifact_path": str(gap_path),
                    "lean_statement": gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [
                        {
                            "name": "StatInference.ProbabilityTheory.durrett2019_example_4_2_3_productProcess_martingale_of_iIndepFun_meanOne"
                        }
                    ],
                    "primitive_formal_source_hits": {
                        primitive: [
                            {
                                "name": "StatInference.ProbabilityTheory.durrett2019_example_4_2_3_productProcess_martingale_of_iIndepFun_meanOne"
                            }
                        ]
                        for primitive in primitives
                    },
                },
            ],
        }
        (run_dir / "q_seq.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        for primitive in primitives:
            self.assertIn(
                "independent_event_indicator_product_lintegral_eq_mul",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertEqual(rows[primitive]["priority_band"], "BRIDGE_REUSE_READY")
        for primitive in (
            "adapted_product_process",
            "bernoulli_likelihood_ratio",
            "conditional_expectation_product_step",
            "independent_bernoulli_sequence",
            "martingale_definition",
        ):
            self.assertIn(
                "independent_event_indicator_condExp_filtration_eq_prob",
                rows[primitive]["bridge_candidate_obligations"],
            )
        self.assertIn(
            "independent_real_condExp_natural_eq_mean",
            rows["conditional_expectation_product_step"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "integrable_l1_tendsto_condexp_filtration",
            rows["conditional_expectation_product_step"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "independent_real_condExp_natural_eq_mean",
            rows["martingale_definition"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "integrable_ae_tendsto_condexp_filtration",
            rows["martingale_definition"]["bridge_candidate_obligations"],
        )

    def test_formalization_target_audit_maps_lln_clt_primitives_to_independent_condexp_bridge(self) -> None:
        run_dir = Path("runs/test_formalization_target_independent_real_condexp_run")
        out_dir = Path("runs/test_formalization_target_independent_real_condexp_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        gap_path = gap_dir / "sample_moment_lln.lean"
        primitives = (
            "sample_moment_lln",
            "iid_empirical_mean_clt",
            "exogeneity_moment_condition",
            "conditional_expectation",
            "iterated_expectation",
            "slutsky_theorem",
            "matrix_inverse_continuous_mapping",
            "tail_quantile_continuous_mapping",
        )
        gap_path.write_text("FORMAL_GAP " + " ".join(primitives), encoding="utf-8")
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps({"questions": [{"question": "q_lln", "formal": {"gaps": 1}}]}),
            encoding="utf-8",
        )
        proof_obligations = (
            "iid_real_clt_tendsto_distribution",
            "independent_real_condExp_natural_eq_mean",
            "condexp_integral_eq_integral_real",
            "finite_sample_mean_unbiased",
            "finite_sample_mean_variance_indep",
        )
        trace = {
            "question": {"id": "q_lln"},
            "problem": {"problem_class": "heteroskedastic_regression_inference"},
            "procedures": [],
            "knowledge": [{"id": "heteroskedastic_regression_hc"}],
            "theorem_goals": [
                {
                    "id": "ols_consistency",
                    "title": "OLS consistency",
                    "proof_strategy": "Use sample-moment laws and exogeneity.",
                    "required_primitives": list(primitives),
                    "proof_obligations": list(proof_obligations),
                },
            ],
            "formal_subclaims": [
                *[
                    {"status": "PROVED", "proof_obligation_id": obligation_id}
                    for obligation_id in proof_obligations
                ],
                {
                    "id": "gap:ols_consistency",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "full LLN/CLT still requires library work",
                    "artifact_path": str(gap_path),
                    "lean_statement": gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "ProbabilityTheory.iIndepFun.condExp_natural_ae_eq_of_lt"}],
                    "primitive_formal_source_hits": {
                        primitive: [{"name": "ProbabilityTheory.iIndepFun.condExp_natural_ae_eq_of_lt"}]
                        for primitive in primitives
                    },
                },
            ],
        }
        (run_dir / "q_lln.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        for primitive in (
            "sample_moment_lln",
            "iid_empirical_mean_clt",
            "exogeneity_moment_condition",
            "conditional_expectation",
        ):
            self.assertIn(
                "independent_real_condExp_natural_eq_mean",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertEqual(rows[primitive]["priority_band"], "BRIDGE_REUSE_READY")
        for primitive in ("exogeneity_moment_condition", "conditional_expectation"):
            self.assertIn(
                "condexp_integral_eq_integral_real",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertIn(
                "condexp_tower_of_sub_sigma_real",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertIn(
                "integrable_l1_tendsto_condexp_filtration",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertIn(
                "integrable_ae_tendsto_condexp_filtration",
                rows[primitive]["bridge_candidate_obligations"],
            )
        self.assertIn(
            "condexp_tower_of_sub_sigma_real",
            rows["iterated_expectation"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "integrable_l1_tendsto_condexp_filtration",
            rows["iterated_expectation"]["bridge_candidate_obligations"],
        )
        for primitive in ("sample_moment_lln", "iid_empirical_mean_clt"):
            self.assertIn(
                "iid_real_clt_tendsto_distribution",
                rows[primitive]["bridge_candidate_obligations"],
            )
        self.assertIn(
            "slutsky_add_negligible_zero_real",
            rows["slutsky_theorem"]["bridge_candidate_obligations"],
        )
        for primitive in ("matrix_inverse_continuous_mapping", "tail_quantile_continuous_mapping"):
            self.assertIn(
                "tendsto_in_distribution_continuous_mapping",
                rows[primitive]["bridge_candidate_obligations"],
            )

    def test_formalization_target_audit_maps_survival_martingale_primitives_to_convergence_bridge(self) -> None:
        run_dir = Path("runs/test_formalization_target_survival_martingale_run")
        out_dir = Path("runs/test_formalization_target_survival_martingale_audit")
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(out_dir, ignore_errors=True)
        gap_dir = run_dir / "formal_gaps"
        gap_dir.mkdir(parents=True, exist_ok=True)
        gap_path = gap_dir / "kaplan_meier_fixed_time_asymptotic_normality.lean"
        primitives = (
            "nelson_aalen_martingale_decomposition",
            "survival_martingale_clt",
            "greenwood_variance_consistency",
        )
        gap_path.write_text("FORMAL_GAP " + " ".join(primitives), encoding="utf-8")
        (run_dir / "research_benchmark_manifest.json").write_text(
            json.dumps({"questions": [{"question": "q_survival", "formal": {"gaps": 1}}]}),
            encoding="utf-8",
        )
        proof_obligations = (
            "event_indicator_expectation",
            "martingale_ae_eq_condexp_limit_process",
            "submartingale_l1_tendsto_limit_process",
            "submartingale_ae_tendsto_limit_process",
            "submartingale_expected_stopped_value_mono",
        )
        trace = {
            "question": {"id": "q_survival"},
            "problem": {"problem_class": "right_censored_survival_inference"},
            "procedures": [],
            "knowledge": [{"id": "kaplan_meier_fixed_time"}],
            "theorem_goals": [
                {
                    "id": "kaplan_meier_fixed_time_asymptotic_normality",
                    "title": "Kaplan-Meier fixed-time asymptotic normality",
                    "proof_strategy": "Use Nelson-Aalen martingale decomposition and martingale convergence.",
                    "required_primitives": list(primitives),
                    "proof_obligations": list(proof_obligations),
                },
            ],
            "formal_subclaims": [
                *[
                    {"status": "PROVED", "proof_obligation_id": obligation_id}
                    for obligation_id in proof_obligations
                ],
                {
                    "id": "gap:kaplan_meier_fixed_time_asymptotic_normality",
                    "status": "FORMAL_GAP",
                    "claim_type": "theory_gap",
                    "gap_reason": "full survival martingale CLT still requires library work",
                    "artifact_path": str(gap_path),
                    "lean_statement": gap_path.read_text(encoding="utf-8"),
                    "formal_source_hits": [{"name": "Submartingale.ae_tendsto_limitProcess"}],
                    "primitive_formal_source_hits": {
                        primitive: [{"name": "Submartingale.ae_tendsto_limitProcess"}]
                        for primitive in primitives
                    },
                },
            ],
        }
        (run_dir / "q_survival.json").write_text(json.dumps(trace), encoding="utf-8")

        payload = audit_formalization_targets(run_dir, out_dir)
        rows = {row["primitive"]: row for row in payload["rows"]}
        for primitive in ("survival_martingale_clt", "nelson_aalen_martingale_decomposition"):
            self.assertIn(
                "martingale_ae_eq_condexp_limit_process",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertIn(
                "submartingale_l1_tendsto_limit_process",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertIn(
                "submartingale_ae_tendsto_limit_process",
                rows[primitive]["bridge_candidate_obligations"],
            )
            self.assertEqual(rows[primitive]["priority_band"], "BRIDGE_REUSE_READY")
        self.assertIn(
            "martingale_ae_eq_condexp_limit_process",
            rows["greenwood_variance_consistency"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "submartingale_l1_tendsto_limit_process",
            rows["greenwood_variance_consistency"]["bridge_candidate_obligations"],
        )
        self.assertIn(
            "submartingale_ae_tendsto_limit_process",
            rows["greenwood_variance_consistency"]["bridge_candidate_obligations"],
        )

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

    def test_autoform_target_export_writes_target_yaml_and_book(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))[:2]
            await run_research_benchmark(
                questions,
                Path("runs/test_autoform_target_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )
            return export_autoform_targets(
                Path("runs/test_autoform_target_run"),
                Path("runs/test_autoform_targets"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertGreater(payload["n_targets"], 0)
        self.assertEqual(payload["n_ok"], payload["n_targets"])
        first = payload["targets"][0]
        self.assertTrue(first["name"].startswith("formal_gap:"))
        self.assertEqual(first["kind"], "theorem")
        self.assertTrue(first["lean_declaration"])
        self.assertNotEqual(first["lean_declaration"], "skeleton.")
        self.assertTrue(first["lean_declaration"].endswith("_skeleton"))
        self.assertTrue(first["lean_file"].endswith(".lean"))
        self.assertIn("FORMAL_GAP", first["description"])
        yaml_path = Path(payload["autoform_targets_yaml"])
        book_path = Path(payload["autoform_book_markdown"])
        self.assertTrue(yaml_path.exists())
        self.assertTrue(book_path.exists())
        yaml_text = yaml_path.read_text(encoding="utf-8")
        self.assertIn("lean_declaration", yaml_text)
        self.assertIn(first["lean_declaration"], yaml_text)
        self.assertIn("autoform.eval run", payload["command_templates"][0])
        self.assertTrue(Path("runs/test_autoform_targets/autoform_targets_manifest.json").exists())
        self.assertTrue(Path("runs/test_autoform_targets/autoform_targets.md").exists())

    def test_proof_bank_expansion_export_writes_legacy_proposal_queue(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))[:2]
            await run_research_benchmark(
                questions,
                Path("runs/test_proof_bank_expansion_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )
            return export_proof_bank_expansion_candidates(
                Path("runs/test_proof_bank_expansion_run"),
                Path("runs/test_proof_bank_expansion"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertGreater(payload["n_candidates"], 0)
        self.assertEqual(payload["n_ok"], payload["n_candidates"])
        self.assertGreater(payload["n_bridge_ready"], 0)
        self.assertGreater(payload["n_blocked_placeholder"], 0)
        first = payload["candidates"][0]
        self.assertTrue(first["proposal_id"].startswith("lemma_proposal:"))
        self.assertEqual(first["source_kind"], "formal_gap_task_export")
        self.assertEqual(first["proposed_by"], "proof_bank_expansion_export")
        self.assertTrue(first["candidate"]["name"].startswith("AIStatistician.Proposed."))
        self.assertTrue(first["candidate"]["statement"].startswith("theorem "))
        self.assertEqual(first["candidate"]["proof"], "")
        self.assertIn(
            first["action_class"],
            {
                "compose_existing_bridge_chain",
                "add_minimal_wrapper",
                "design_bridge_lemma",
                "design_from_first_principles",
            },
        )
        self.assertTrue(first["candidate"]["motivation_tasks"])
        self.assertTrue(first["source_task_ids"])
        self.assertTrue(first["expected_premises"])
        self.assertIn("lean_compiles", first["required_gates"])
        self.assertIn(first["status"], {"blocked_placeholder", "candidate_ready"})
        queue = payload["theorem_hole_promotion_queue"]
        self.assertEqual(queue["queued_count"], payload["n_candidates"])
        self.assertTrue(queue["queue"])
        self.assertTrue(queue["queue"][0]["expected_premises"])
        self.assertIn("action_class", queue["queue"][0])
        self.assertIn("next_action", queue["queue"][0])
        self.assertIn("bridge_chain_order", queue["queue"][0])
        self.assertIn("remaining_interface", queue["queue"][0])
        self.assertEqual(
            payload["n_candidates"],
            payload["n_compose_existing_bridge_chain"]
            + payload["n_add_minimal_wrapper"]
            + payload["n_design_bridge_lemma"]
            + payload["n_design_from_first_principles"],
        )
        compose_rows = [
            row for row in payload["candidates"] if row["action_class"] == "compose_existing_bridge_chain"
        ]
        if compose_rows:
            self.assertTrue(compose_rows[0]["candidate"]["name"].endswith("_theorem_composition"))
            self.assertIn("Avoid duplicating bridge wrappers", compose_rows[0]["notes"])
            plan = compose_rows[0]["candidate"]["composition_plan"]
            self.assertEqual(
                plan["strategy"],
                "compose_verified_bridge_chain_into_theorem_skeleton",
            )
            self.assertTrue(plan["ordered_obligation_ids"])
            self.assertTrue(plan["ordered_obligations"])
            self.assertTrue(plan["remaining_interface"])
            self.assertIn("not itself a Lean proof", plan["proof_evidence_boundary"])
        self.assertTrue(Path("runs/test_proof_bank_expansion/proof_bank_expansion_manifest.json").exists())
        self.assertTrue(Path("runs/test_proof_bank_expansion/lemma_proposals.jsonl").exists())
        self.assertTrue(Path("runs/test_proof_bank_expansion/theorem_hole_promotion_queue_manifest.json").exists())
        rows = [
            json.loads(line)
            for line in Path("runs/test_proof_bank_expansion/lemma_proposals.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(len(rows), payload["n_candidates"])
        self.assertIn("blocked_reasons", rows[0])
        self.assertIn("action_class", rows[0])

    def test_primitive_source_coverage_audit_classifies_missing_primitives(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))[:2]
            await run_research_benchmark(
                questions,
                Path("runs/test_primitive_source_coverage_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=15,
                seed=20260602,
            )
            return audit_primitive_source_coverage(
                Path("runs/test_primitive_source_coverage_run"),
                Path("runs/test_primitive_source_coverage"),
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertGreater(payload["n_primitives"], 0)
        self.assertEqual(
            payload["n_primitives"],
            payload["n_direct_wrapper_possible"]
            + payload["n_bridge_lemma_needed"]
            + payload["n_source_only_not_importable"]
            + payload["n_no_source_found"],
        )
        self.assertGreater(
            payload["n_direct_wrapper_possible"] + payload["n_bridge_lemma_needed"],
            0,
        )
        first = payload["rows"][0]
        self.assertIn(
            first["classification"],
            {
                "direct_wrapper_possible",
                "bridge_lemma_needed",
                "source_only_not_importable",
                "no_source_found",
            },
        )
        self.assertIn(
            first["action_class"],
            {
                "compose_existing_bridge_chain",
                "add_minimal_wrapper",
                "design_bridge_lemma",
                "port_external_source",
                "design_from_first_principles",
            },
        )
        self.assertEqual(
            payload["n_primitives"],
            payload["n_compose_existing_bridge_chain"]
            + payload["n_add_minimal_wrapper"]
            + payload["n_design_bridge_lemma"]
            + payload["n_port_external_source"]
            + payload["n_design_from_first_principles"],
        )
        self.assertTrue(payload["by_action_class"])
        self.assertIn("Retrieval hits are not proof evidence", " ".join(payload["limitations"]))
        self.assertTrue(Path("runs/test_primitive_source_coverage/primitive_source_coverage_manifest.json").exists())
        self.assertTrue(Path("runs/test_primitive_source_coverage/primitive_source_coverage.md").exists())

    def test_research_training_export_writes_agent_sft_and_grpo_data(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))[:2]
            await run_research_benchmark(
                questions,
                Path("runs/test_research_training_run"),
                proof_verifier=MockProofVerifier(),
                n_runs=25,
                seed=20260528,
            )
            return export_research_training_dataset(
                Path("runs/test_research_training_run"),
                Path("runs/test_research_training_export"),
                validation_fraction=0.25,
            )

        payload = asyncio.run(run())
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_traces"], 2)
        self.assertGreaterEqual(payload["n_sft_examples"], 8)
        self.assertEqual(payload["n_train"] + payload["n_validation"], payload["n_sft_examples"])
        self.assertEqual(payload["n_grpo_tasks"], 2)
        self.assertIn("atlas_lean_high_dimensional_statistics", payload["excluded_no_training_sources"])
        for task in (
            "problem_formalization",
            "theory_plan_generation",
            "formal_gap_routing",
            "simulation_critique",
        ):
            self.assertEqual(payload["by_task"][task], 2)
        train = Path(payload["train_jsonl"])
        validation = Path(payload["validation_jsonl"])
        all_jsonl = Path(payload["all_jsonl"])
        grpo_jsonl = Path(payload["grpo_jsonl"])
        self.assertTrue(train.exists())
        self.assertTrue(validation.exists())
        self.assertTrue(all_jsonl.exists())
        self.assertTrue(grpo_jsonl.exists())
        rows = [json.loads(line) for line in all_jsonl.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), payload["n_sft_examples"])
        self.assertTrue(all(row["completion"].strip().startswith("{") for row in rows))
        serialized_rows = json.dumps(rows)
        self.assertNotIn("atlas_lean_high_dimensional_statistics", serialized_rows)
        self.assertNotIn("atlas_lean_theory_of_probability", serialized_rows)
        legacy = json.loads(Path(payload["legacy_training_manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(legacy["base_model"], "untrained-trace-export")
        self.assertEqual(len(legacy["sft_examples"]), payload["n_sft_examples"])
        self.assertEqual(len(legacy["grpo_tasks"]), payload["n_grpo_tasks"])
        self.assertTrue(Path("runs/test_research_training_export/research_training_manifest.json").exists())
        self.assertTrue(Path("runs/test_research_training_export/research_training.md").exists())

    def test_source_training_export_policy_has_owner_override(self) -> None:
        self.assertFalse(source_allows_training_export("atlas_lean_high_dimensional_statistics"))
        self.assertFalse(source_allows_training_export("brownian_motion_lean"))
        self.assertFalse(source_allows_training_export("scilean_calculus"))
        self.assertTrue(source_allows_training_export("formal_slt"))
        self.assertTrue(source_allows_training_export("lean_rademacher"))
        self.assertTrue(source_allows_training_export("lean_machine_learning_lml"))
        self.assertTrue(source_allows_training_export("kolmogorov_extension_lean"))
        with patch.dict(
            "os.environ",
            {"AI_STATISTICIAN_INCLUDE_EXTERNAL_TRAINING_SOURCES": "1"},
        ):
            self.assertTrue(source_allows_training_export("atlas_lean_high_dimensional_statistics"))
            self.assertTrue(source_allows_training_export("brownian_motion_lean"))
            self.assertTrue(source_allows_training_export("scilean_calculus"))

    def test_research_policy_baseline_scores_exported_agent_examples(self) -> None:
        out = Path("runs/test_research_policy_baseline_fixture")
        out.mkdir(parents=True, exist_ok=True)
        train = out / "train.jsonl"
        validation = out / "validation.jsonl"
        train_rows = [
            {
                "example_id": "train:formalize:causal",
                "task": "problem_formalization",
                "prompt": "causal ATE binary treatment positivity",
                "completion": json.dumps({"problem_class": "semiparametric_causal_ate", "estimand": "ATE"}),
                "question_id": "causal_ate_aipw",
                "problem_class": "semiparametric_causal_ate",
                "procedure_ids": ["oracle_aipw_ate"],
                "theorem_goal_ids": ["aipw_double_robustness"],
                "tags": ["research_trace", "problem_formalization", "semiparametric_causal_ate"],
            },
            {
                "example_id": "train:sim:causal",
                "task": "simulation_critique",
                "prompt": "causal ATE simulation coverage bias rmse",
                "completion": json.dumps({"passed": True, "recommended_route": "accept"}),
                "question_id": "causal_ate_aipw",
                "problem_class": "semiparametric_causal_ate",
                "procedure_ids": ["oracle_aipw_ate"],
                "theorem_goal_ids": ["aipw_double_robustness"],
                "tags": ["research_trace", "simulation_critique", "semiparametric_causal_ate"],
            },
        ]
        validation_rows = [
            {
                "example_id": "val:formalize:causal",
                "task": "problem_formalization",
                "prompt": "paper asks average treatment effect with binary treatment and positivity",
                "completion": json.dumps({"problem_class": "semiparametric_causal_ate", "estimand": "ATE"}),
                "question_id": "causal_ate_holdout",
                "problem_class": "semiparametric_causal_ate",
                "procedure_ids": ["oracle_aipw_ate"],
                "theorem_goal_ids": ["aipw_double_robustness"],
                "tags": ["research_trace", "problem_formalization", "semiparametric_causal_ate"],
            }
        ]
        train.write_text("\n".join(json.dumps(row) for row in train_rows) + "\n", encoding="utf-8")
        validation.write_text("\n".join(json.dumps(row) for row in validation_rows) + "\n", encoding="utf-8")

        payload = evaluate_research_policy_baseline(
            train,
            validation,
            Path("runs/test_research_policy_baseline"),
            k=2,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_train"], 2)
        self.assertEqual(payload["n_validation"], 1)
        self.assertEqual(payload["same_task"], 1)
        self.assertEqual(payload["same_problem_class"], 1)
        self.assertEqual(payload["predicted_valid_json"], 1)
        self.assertGreater(payload["mean_json_key_f1"], 0)
        self.assertTrue(Path(payload["predictions_jsonl"]).exists())
        rows = [
            json.loads(line)
            for line in Path(payload["predictions_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["predicted_from_task"], "problem_formalization")

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
        self.assertEqual(report["frontier_summary"]["n_supported"], 60)
        self.assertEqual(report["frontier_summary"]["n_unsupported"], 0)

        manifest = write_research_capability_audit(report, Path("runs/test_research_capability_audit"))
        self.assertTrue(manifest.exists())
        self.assertTrue(Path("runs/test_research_capability_audit/research_capability_audit.md").exists())
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertFalse(payload["goal_complete"])
        self.assertTrue(payload["all_current_release_requirements_met"])

    def test_architecture_audit_marks_queued_feedback_not_live_loop(self) -> None:
        payload = audit_architecture(Path("runs/test_architecture_audit"))
        self.assertEqual(
            payload["architecture_status"],
            "PARTIAL_LIVE_FEEDBACK_LOOP_WITH_SCOPED_AUTONOMY",
        )
        self.assertTrue(payload["is_current_architecture_correct_for_release_scaffold"])
        self.assertFalse(payload["is_current_architecture_correct_for_full_autonomous_ai_statistician"])
        self.assertEqual(payload["implemented_feedback_mode"], "bounded_research_loop_over_next_iteration_agenda")
        self.assertTrue(payload["has_live_revision_loop"])
        self.assertTrue(payload["has_registered_live_repair_handler_interface"])
        self.assertTrue(payload["all_release_scaffold_components_present"])

        statuses = {row["component"]: row["status"] for row in payload["components"]}
        self.assertEqual(statuses["feedback_router"], "ACHIEVED")
        self.assertEqual(statuses["live_revision_loop"], "PARTIAL")
        self.assertEqual(statuses["llm_theory_developer"], "PARTIAL")
        live_loop = next(row for row in payload["components"] if row["component"] == "live_revision_loop")
        self.assertTrue(any("DefaultProofEngineer" in item for item in live_loop["evidence"]))
        self.assertTrue(any("DefaultTheoryDeveloper" in item for item in live_loop["evidence"]))
        route_by_trigger = {row["trigger"]: row for row in payload["feedback_routes"]}
        self.assertEqual(route_by_trigger["THEORY_OR_PROCEDURE_ISSUE"]["owner_agent"], "theory_developer")
        self.assertEqual(
            route_by_trigger["THEORY_OR_PROCEDURE_ISSUE"]["live_execution_status"],
            "EXECUTABLE_SCOPED_THEORY_REVISION_PROPOSAL",
        )
        self.assertEqual(
            route_by_trigger["IMPLEMENTATION_OR_NUMERICAL_ISSUE"]["owner_agent"],
            "algorithm_engineer",
        )
        self.assertEqual(
            route_by_trigger["IMPLEMENTATION_OR_NUMERICAL_ISSUE"]["live_execution_status"],
            "EXECUTABLE_SCOPED_ALGORITHM_REPAIR_PROPOSAL",
        )
        self.assertTrue(any("DefaultAlgorithmEngineer" in item for item in live_loop["evidence"]))
        self.assertEqual(
            route_by_trigger["FORMAL_GAP"]["live_execution_status"],
            "EXECUTABLE_DEFAULT_PROOF_BANK_BRIDGE_OR_RETRIEVAL_REVIEW",
        )
        self.assertEqual(
            route_by_trigger["FAILED_PROOF_OBLIGATION"]["live_execution_status"],
            "EXECUTABLE_DEFAULT_REGISTERED_OBLIGATION_REPAIR_OR_REGISTERED_HANDLER",
        )
        self.assertTrue(Path("runs/test_architecture_audit/architecture_audit_manifest.json").exists())
        self.assertTrue(Path("runs/test_architecture_audit/architecture_audit.md").exists())

    def test_research_loop_executes_mc_precision_rerun(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        procedure, theorem_goal = TheoryPlanner().plan(problem)
        low_precision_sim = ResearchSimulator(n_runs=5, seed=7).run(problem, procedure)[0]
        low_precision_sim.passed = False
        low_precision_sim.diagnosis.status = "INSUFFICIENT_MC_PRECISION"
        low_precision_sim.diagnosis.escalate_to = "rerun_more_mc"
        low_precision_sim.diagnosis.rationale = "test forces a Monte Carlo precision rerun"
        ok_sim = ResearchSimulator(n_runs=25, seed=8).run(problem, procedure)[0]
        ok_sim.passed = True
        ok_sim.diagnosis.status = "OK"
        ok_sim.diagnosis.escalate_to = "none"
        ok_sim.diagnosis.rationale = "test second round passes"

        first = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[low_precision_sim],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "simulation:test",
                            "owner_agent": "simulator_agent",
                            "trigger": "INSUFFICIENT_MC_PRECISION",
                            "action": "rerun_with_larger_monte_carlo_budget",
                            "evidence": "test precision",
                        }
                    ]
                }
            },
            status="SIMULATION_FLAGGED_WITH_FORMAL_GAPS",
        )
        second = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[ok_sim],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "monitor:test",
                            "owner_agent": "research_coordinator",
                            "trigger": "NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
                            "action": "archive_trace_or_expand_benchmark_stress_tests",
                            "evidence": "test monitor",
                        }
                    ]
                }
            },
            status="RESEARCH_TRACE_READY_WITH_FORMAL_GAPS",
        )
        reports = [first, second]
        seen_n_runs = []

        class FakeLab:
            def __init__(self, report):
                self.report = report

            async def run(self, question):
                return self.report

        def factory(n_runs, seed):
            seen_n_runs.append(n_runs)
            return FakeLab(reports.pop(0))

        result = asyncio.run(
            ResearchLoopCoordinator(n_runs=5, seed=7, lab_factory=factory).iterate(
                question,
                max_rounds=2,
                mc_rerun_multiplier=3,
            )
        )
        self.assertEqual(result["status"], "CONVERGED_MONITOR_READY")
        self.assertEqual(result["n_rounds"], 2)
        self.assertEqual(seen_n_runs, [5, 15])
        self.assertEqual(
            result["rounds"][0]["actions"][0]["execution_status"],
            "EXECUTED_RERUN_MORE_MC",
        )
        self.assertEqual(
            result["rounds"][1]["actions"][0]["execution_status"],
            "EXECUTED_MONITOR",
        )

    def test_research_loop_default_theory_developer_proposes_scoped_revision(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        procedure, theorem_goal = TheoryPlanner().plan(problem)
        bad_sim = ResearchSimulator(n_runs=25, seed=11).run(problem, procedure)[0]
        bad_sim.passed = False
        bad_sim.diagnosis.status = "THEORY_OR_PROCEDURE_ISSUE"
        bad_sim.diagnosis.escalate_to = "theory_developer"
        bad_sim.diagnosis.failed_diagnostics = ("coverage",)
        bad_sim.diagnosis.rationale = "test forces theory revision"

        first = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[bad_sim],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "simulation:theory",
                            "owner_agent": "theory_developer",
                            "trigger": "THEORY_OR_PROCEDURE_ISSUE",
                            "action": "revise_estimator_or_theorem_acceptance_rule",
                            "evidence": "coverage below threshold",
                            "failed_diagnostics": ["coverage"],
                            "target_procedure": procedure[0].id,
                        }
                    ]
                }
            },
            status="SIMULATION_FLAGGED_WITH_FORMAL_GAPS",
        )
        second = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "monitor:test",
                            "owner_agent": "research_coordinator",
                            "trigger": "NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
                            "action": "archive_trace_or_expand_benchmark_stress_tests",
                            "evidence": "test monitor after applied theory revision",
                        }
                    ]
                }
            },
            status="RESEARCH_TRACE_READY_WITH_FORMAL_GAPS",
        )
        reports = [first, second]

        class FakeLab:
            def __init__(self, report):
                self.report = report

            async def run(self, question):
                return self.report

        def factory(n_runs, seed):
            return FakeLab(reports.pop(0))

        result = asyncio.run(
            ResearchLoopCoordinator(n_runs=25, seed=11, lab_factory=factory).iterate(
                question,
                max_rounds=2,
            )
        )
        self.assertEqual(result["status"], "CONVERGED_MONITOR_READY")
        self.assertTrue(result["honesty_boundary"]["executes_default_theory_developer_revision_handler"])
        self.assertEqual(result["n_theory_revisions"], 1)
        action = result["rounds"][0]["actions"][0]
        self.assertEqual(action["execution_status"], "EXECUTED_SCOPED_THEORY_REVISION_PROPOSAL")
        self.assertTrue(action["repair_contract_ok"])
        self.assertEqual(action["live_repair_handler"], "DefaultTheoryDeveloper")
        self.assertTrue(action["rerun_requested"])
        self.assertIn("coverage", action["repair_artifact"]["failure_class"])
        self.assertIn("revised_theorem_goals", action["repair_artifact"])
        self.assertEqual(result["rounds"][1]["actions"][0]["execution_status"], "EXECUTED_MONITOR")
        task = action["repair_task"]
        self.assertEqual(task["owner_agent"], "theory_developer")
        self.assertEqual(task["task_type"], "theory_revision_from_simulation_failure")
        self.assertIn("revised_theorem_goals", task["output_contract"]["required_fields"])
        self.assertTrue(any("simulation" in item for item in task["acceptance_criteria"]))

    def test_default_theory_developer_handles_selection_failures(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        procedures, theorem_goals = TheoryPlanner().plan(problem)
        report = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedures,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[],
            theorem_goals=theorem_goals,
            theory_plan={"next_iteration_agenda": {"items": []}},
            status="SIMULATION_FLAGGED_WITH_FORMAL_GAPS",
        )
        artifact = DefaultTheoryDeveloper().repair_theory_issue(
            {
                "owner_agent": "theory_developer",
                "trigger": "THEORY_OR_PROCEDURE_ISSUE",
                "failed_diagnostics": ["selection_accuracy"],
                "target_procedure": procedures[0].id,
            },
            report,
        )
        self.assertIsNotNone(artifact)
        repair = artifact["repair_artifact"]
        self.assertEqual(repair["failure_class"], "selection_or_screening_failure")
        self.assertIn("screening_selection_accuracy_under_signal_separation", repair["revised_theorem_goals"])
        self.assertIn("selection_accuracy_lower_bound_from_support_events", repair["next_formal_obligations"])

    def test_theory_revision_overlay_enters_lab_theorem_roadmap(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        revision = {
            "artifact_id": "theory_revision:test",
            "target_procedure": "oracle_aipw_ate",
            "repair_artifact": {
                "target_procedure": "oracle_aipw_ate",
                "revised_procedure": "oracle_aipw_ate:calibrated_interval_variant",
                "revised_theorem_goals": [
                    "coverage_lower_bound_under_declared_dgp",
                    "standard_error_or_quantile_calibration",
                ],
                "assumption_delta": ["separate point consistency from interval calibration"],
                "expected_simulation_delta": "coverage should improve under the declared DGP",
                "failure_class": "coverage_or_standard_error_failure",
                "next_formal_obligations": ["coverage_lower_bound_of_complement_error"],
            },
        }

        async def run():
            return await AIStatisticalTheoryLab(
                proof_verifier=MockProofVerifier(),
                n_runs=10,
                seed=20260530,
                theory_revisions=[revision],
            ).run(question)

        report = asyncio.run(run())
        applied = report.theory_plan["applied_theory_revisions"]
        self.assertEqual(len(applied), 1)
        self.assertTrue(applied[0]["algorithm_unchanged"])
        procedure_row = report.theory_plan["candidate_procedures"][0]
        self.assertEqual(procedure_row["id"], "oracle_aipw_ate_calibrated_interval_variant")
        self.assertEqual(procedure_row["algorithm"], "oracle_aipw")
        roadmap_ids = {row["id"] for row in report.theory_plan["theorem_roadmap"]}
        self.assertIn("coverage_lower_bound_under_declared_dgp", roadmap_ids)
        self.assertIn("standard_error_or_quantile_calibration", roadmap_ids)
        formal_gap_ids = {row.id.split(":")[-1] for row in report.formal_subclaims if row.status == "FORMAL_GAP"}
        self.assertIn("coverage_lower_bound_under_declared_dgp", formal_gap_ids)
        proved_ids = {
            row.proof_obligation_id
            for row in report.formal_subclaims
            if row.status == "PROVED"
        }
        self.assertIn("coverage_lower_bound_of_complement_error", proved_ids)

    def test_research_loop_executes_registered_live_theory_repair_handler(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        procedure, theorem_goal = TheoryPlanner().plan(problem)
        bad_sim = ResearchSimulator(n_runs=25, seed=13).run(problem, procedure)[0]
        bad_sim.passed = False
        bad_sim.diagnosis.status = "THEORY_OR_PROCEDURE_ISSUE"
        bad_sim.diagnosis.escalate_to = "theory_developer"
        bad_sim.diagnosis.failed_diagnostics = ("coverage",)
        bad_sim.diagnosis.rationale = "test forces live theory repair"
        ok_sim = ResearchSimulator(n_runs=25, seed=14).run(problem, procedure)[0]
        ok_sim.passed = True
        ok_sim.diagnosis.status = "OK"
        ok_sim.diagnosis.escalate_to = "none"
        ok_sim.diagnosis.rationale = "test live repair second round passes"

        first = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[bad_sim],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "simulation:theory",
                            "owner_agent": "theory_developer",
                            "trigger": "THEORY_OR_PROCEDURE_ISSUE",
                            "action": "revise_estimator_or_theorem_acceptance_rule",
                            "evidence": "coverage below threshold",
                            "failed_diagnostics": ["coverage"],
                            "target_procedure": procedure[0].id,
                        }
                    ]
                }
            },
            status="SIMULATION_FLAGGED_WITH_FORMAL_GAPS",
        )
        second = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[ok_sim],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "monitor:test",
                            "owner_agent": "research_coordinator",
                            "trigger": "NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
                            "action": "archive_trace_or_expand_benchmark_stress_tests",
                            "evidence": "test monitor",
                        }
                    ]
                }
            },
            status="RESEARCH_TRACE_READY_WITH_FORMAL_GAPS",
        )
        reports = [first, second]
        handler_calls = []

        class FakeLab:
            def __init__(self, report):
                self.report = report

            async def run(self, question):
                return self.report

        def factory(n_runs, seed):
            return FakeLab(reports.pop(0))

        def live_theory_handler(item, report):
            handler_calls.append((item["id"], report.question.id))
            return {
                "execution_status": "EXECUTED_THEORY_REVISION",
                "task_type": "theory_revision_from_simulation_failure",
                "result": "Test handler revised the theorem plan and requested a rerun.",
                "rerun_requested": True,
                "revision_artifact": {
                    "revised_theorem_goals": ["test_revised_goal"],
                    "assumption_delta": [],
                },
                "repair_artifact": {
                    "revised_procedure": procedure[0].id,
                    "revised_theorem_goals": ["test_revised_goal"],
                    "assumption_delta": ["coverage diagnostic requires revised standard-error theorem"],
                    "expected_simulation_delta": "coverage diagnostic should pass on rerun",
                },
            }

        result = asyncio.run(
            ResearchLoopCoordinator(
                n_runs=25,
                seed=13,
                lab_factory=factory,
                repair_handlers={"THEORY_OR_PROCEDURE_ISSUE": live_theory_handler},
            ).iterate(
                question,
                max_rounds=2,
            )
        )
        self.assertEqual(result["status"], "CONVERGED_MONITOR_READY")
        self.assertTrue(result["honesty_boundary"]["executes_registered_live_repair_handlers"])
        self.assertEqual(handler_calls, [("simulation:theory", question.id)])
        action = result["rounds"][0]["actions"][0]
        self.assertEqual(action["execution_status"], "EXECUTED_THEORY_REVISION")
        self.assertTrue(action["rerun_requested"])
        self.assertTrue(action["repair_contract_ok"])
        self.assertEqual(result["rounds"][1]["actions"][0]["execution_status"], "EXECUTED_MONITOR")

    def test_research_loop_blocks_invalid_live_repair_handler_artifact(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        procedure, theorem_goal = TheoryPlanner().plan(problem)
        bad_sim = ResearchSimulator(n_runs=25, seed=15).run(problem, procedure)[0]
        bad_sim.passed = False
        bad_sim.diagnosis.status = "THEORY_OR_PROCEDURE_ISSUE"
        bad_sim.diagnosis.escalate_to = "theory_developer"
        bad_sim.diagnosis.failed_diagnostics = ("coverage",)
        bad_sim.diagnosis.rationale = "test invalid repair artifact"

        report = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[bad_sim],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "simulation:theory",
                            "owner_agent": "theory_developer",
                            "trigger": "THEORY_OR_PROCEDURE_ISSUE",
                            "action": "revise_estimator_or_theorem_acceptance_rule",
                            "evidence": "coverage below threshold",
                        }
                    ]
                }
            },
            status="SIMULATION_FLAGGED_WITH_FORMAL_GAPS",
        )

        class FakeLab:
            async def run(self, question):
                return report

        def invalid_handler(item, report):
            return {
                "execution_status": "EXECUTED_THEORY_REVISION",
                "result": "invalid artifact asks for rerun without required fields",
                "rerun_requested": True,
                "repair_artifact": {"revised_theorem_goals": ["too_small"]},
            }

        result = asyncio.run(
            ResearchLoopCoordinator(
                n_runs=25,
                seed=15,
                lab_factory=lambda _n, _s: FakeLab(),
                repair_handlers={"THEORY_OR_PROCEDURE_ISSUE": invalid_handler},
            ).iterate(
                question,
                max_rounds=2,
            )
        )
        self.assertEqual(result["status"], "REPAIR_HANDLER_CONTRACT_FAILED")
        self.assertEqual(result["n_rounds"], 1)
        action = result["rounds"][0]["actions"][0]
        self.assertEqual(action["execution_status"], "REPAIR_HANDLER_CONTRACT_FAILED")
        self.assertFalse(action["rerun_requested"])
        self.assertFalse(action["repair_contract_ok"])
        self.assertTrue(any("revised_procedure" in err for err in action["repair_contract_errors"]))

    def test_research_loop_default_algorithm_engineer_proposes_scoped_repair(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        procedure, theorem_goal = TheoryPlanner().plan(problem)
        procedure = attach_research_algorithm_metadata(procedure)
        bad_sim = ResearchSimulator(n_runs=25, seed=16).run(problem, procedure)[0]
        bad_sim.passed = False
        bad_sim.metrics["n_runs"] = 25.0
        bad_sim.metrics["n_failed"] = 10.0
        bad_sim.diagnosis.status = "IMPLEMENTATION_OR_NUMERICAL_ISSUE"
        bad_sim.diagnosis.escalate_to = "algorithm_engineer"
        bad_sim.diagnosis.failed_diagnostics = ("n_failed",)
        bad_sim.diagnosis.rationale = "test forces algorithm repair"

        report = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[bad_sim],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "simulation:algorithm",
                            "owner_agent": "algorithm_engineer",
                            "trigger": "IMPLEMENTATION_OR_NUMERICAL_ISSUE",
                            "action": "repair_algorithm_implementation_or_numerical_stability",
                            "evidence": "too many failed replicates",
                            "failed_diagnostics": ["n_failed"],
                            "target_procedure": procedure[0].id,
                        }
                    ]
                }
            },
            status="SIMULATION_FLAGGED_WITH_FORMAL_GAPS",
        )

        class FakeLab:
            async def run(self, question):
                return report

        result = asyncio.run(
            ResearchLoopCoordinator(n_runs=25, seed=16, lab_factory=lambda _n, _s: FakeLab()).iterate(
                question,
                max_rounds=2,
            )
        )
        self.assertEqual(result["status"], "ALGORITHM_REPAIR_PROPOSED")
        self.assertTrue(result["honesty_boundary"]["executes_default_algorithm_engineer_repair_handler"])
        action = result["rounds"][0]["actions"][0]
        self.assertEqual(action["execution_status"], "EXECUTED_SCOPED_ALGORITHM_REPAIR_PROPOSAL")
        self.assertEqual(action["live_repair_handler"], "DefaultAlgorithmEngineer")
        self.assertTrue(action["repair_contract_ok"])
        self.assertFalse(action["rerun_requested"])
        artifact = action["repair_artifact"]
        self.assertEqual(artifact["target_procedure"], procedure[0].id)
        self.assertEqual(len(artifact["implementation_hash"]), 64)
        self.assertEqual(artifact["rerun_metrics"]["n_failed_target"], 0.0)
        self.assertIn("patch_summary", artifact)

    def test_algorithm_repair_promotion_queue_filters_sandbox_candidates(self) -> None:
        loop_dir = Path("runs/test_algorithm_repair_promotion_input")
        loop_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = loop_dir / "research_loop_live_repair_artifacts.jsonl"
        good_artifact = {
            "schema_version": 1,
            "artifact_id": "live_repair:algorithm-good",
            "question_id": "q",
            "round": 1,
            "source_action_id": "simulation:algorithm",
            "owner_agent": "algorithm_engineer",
            "trigger": "IMPLEMENTATION_OR_NUMERICAL_ISSUE",
            "execution_status": "EXECUTED_SCOPED_ALGORITHM_REPAIR_PROPOSAL",
            "task_type": "algorithm_repair_from_numerical_failure",
            "live_repair_handler": "DefaultAlgorithmEngineer",
            "repair_contract_ok": True,
            "repair_contract_errors": [],
            "rerun_requested": False,
            "repair_artifact": {
                "target_procedure": "oracle_aipw_ate",
                "algorithm_id": "oracle_aipw",
                "patch_summary": "Add deterministic finite-value guard.",
                "implementation_hash": "a" * 64,
                "reproduction_test": {"procedure_id": "oracle_aipw_ate", "nonfinite_metrics": ["rmse"]},
                "rerun_metrics": {
                    "n_failed_target": 0.0,
                    "finite_metric_required": 1.0,
                    "max_failed_fraction": 0.05,
                },
                "numerical_repair_kind": "finite_metric_guard",
                "algorithm_registry_status": "vetted",
            },
            "repair_contract": {
                "required_fields": [
                    "patch_summary",
                    "implementation_hash",
                    "reproduction_test",
                    "rerun_metrics",
                ],
                "required_gate": "algorithm audit plus finite simulation metrics",
            },
        }
        artifact_path.write_text(json.dumps(good_artifact) + "\n", encoding="utf-8")
        (loop_dir / "research_loop_manifest.json").write_text(
            json.dumps({"live_repair_artifacts_jsonl": str(artifact_path)}),
            encoding="utf-8",
        )
        payload = export_algorithm_repair_promotion_queue(
            loop_dir,
            Path("runs/test_algorithm_repair_promotion"),
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_candidates"], 1)
        self.assertEqual(payload["n_ok"], 1)
        self.assertEqual(payload["by_sandbox_status"]["READY_FOR_SANDBOX_PATCH"], 1)
        queue_path = Path(payload["queue_jsonl"])
        self.assertTrue(queue_path.exists())
        rows = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows[0]["algorithm_id"], "oracle_aipw")
        self.assertEqual(rows[0]["sandbox_status"], "READY_FOR_SANDBOX_PATCH")

    def test_algorithm_repair_sandbox_validates_current_registry_hash(self) -> None:
        promotion_dir = Path("runs/test_algorithm_repair_sandbox_input")
        promotion_dir.mkdir(parents=True, exist_ok=True)
        spec = attach_research_algorithm_metadata(
            TheoryPlanner().plan(ProblemFormalizer().formalize(load_open_research_questions(Path("examples/research_questions.json"))[0]))[0]
        )[0].algorithm_spec
        self.assertIsNotNone(spec)
        candidate = {
            "candidate_id": "algorithm_repair_candidate:test",
            "artifact_id": "live_repair:algorithm-good",
            "question_id": "q",
            "source_action_id": "simulation:algorithm",
            "target_procedure": "oracle_aipw_ate",
            "algorithm_id": "oracle_aipw",
            "implementation_hash": spec.implementation_hash,
            "numerical_repair_kind": "finite_metric_guard",
            "sandbox_status": "READY_FOR_SANDBOX_PATCH",
            "required_gate": "sandboxed algorithm patch + algorithm audit + finite simulation rerun",
            "ok": True,
            "errors": [],
        }
        queue_path = promotion_dir / "algorithm_repair_promotion_queue.jsonl"
        queue_path.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
        (promotion_dir / "algorithm_repair_promotion_manifest.json").write_text(
            json.dumps({"queue_jsonl": str(queue_path), "n_candidates": 1, "all_ok": True}),
            encoding="utf-8",
        )
        payload = evaluate_algorithm_repair_sandbox(
            promotion_dir,
            Path("runs/test_algorithm_repair_sandbox"),
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_ok"], 1)
        self.assertEqual(payload["by_sandbox_status"]["SANDBOX_PATCH_PLAN_READY"], 1)
        rows = [
            json.loads(line)
            for line in Path(payload["results_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(rows[0]["hash_matches_current_registry"])
        self.assertFalse(rows[0]["patch_applied_to_production"])
        self.assertIn("finite-value", " ".join(rows[0]["allowed_patch_scope"]))

    def test_algorithm_repair_sandbox_apply_records_non_mutating_application(self) -> None:
        sandbox_dir = Path("runs/test_algorithm_repair_sandbox_apply_input")
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        result = {
            "candidate_id": "algorithm_repair_candidate:test",
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "original_implementation_hash": "a" * 64,
            "current_implementation_hash": "a" * 64,
            "hash_matches_current_registry": True,
            "algorithm_audit_ok": True,
            "sandbox_status": "SANDBOX_PATCH_PLAN_READY",
            "patch_applied_to_production": False,
            "allowed_patch_scope": [
                "add finite-value metric guards",
                "record non-finite replicate diagnostics",
                "do not change estimand or theorem statement",
            ],
            "required_next_gate": (
                "apply bounded patch in isolated workspace, rerun algorithm audit, "
                "then rerun finite simulation diagnostics before promotion"
            ),
            "ok": True,
            "errors": [],
        }
        results_path = sandbox_dir / "algorithm_repair_sandbox_results.jsonl"
        results_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
        (sandbox_dir / "algorithm_repair_sandbox_manifest.json").write_text(
            json.dumps({"results_jsonl": str(results_path), "n_candidates": 1, "all_ok": True}),
            encoding="utf-8",
        )
        payload = apply_algorithm_repair_sandbox_results(
            sandbox_dir,
            Path("runs/test_algorithm_repair_sandbox_apply"),
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_candidates"], 1)
        self.assertEqual(payload["n_ok"], 1)
        rows = [
            json.loads(line)
            for line in Path(payload["results_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["patch_application_mode"], "non_mutating_guard_plan")
        self.assertFalse(rows[0]["patch_applied_to_production"])
        self.assertTrue(rows[0]["sandbox_artifact_created"])
        self.assertEqual(rows[0]["rerun_evidence_kind"], "registry_audit_plus_guard_gate")
        self.assertIn("isolated workspace", rows[0]["required_next_gate"])

    def test_algorithm_repair_sandbox_rerun_records_current_registry_evidence(self) -> None:
        apply_dir = Path("runs/test_algorithm_repair_sandbox_rerun_input")
        apply_dir.mkdir(parents=True, exist_ok=True)
        result = {
            "application_id": "algorithm_repair_sandbox_apply:test",
            "candidate_id": "algorithm_repair_candidate:test",
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "patch_application_mode": "non_mutating_guard_plan",
            "patch_applied_to_production": False,
            "sandbox_artifact_created": True,
            "registry_audit_ok": True,
            "rerun_evidence_kind": "registry_audit_plus_guard_gate",
            "allowed_patch_scope": [
                "add finite-value metric guards",
                "record non-finite replicate diagnostics",
                "do not change estimand or theorem statement",
            ],
            "required_next_gate": (
                "apply bounded patch in isolated workspace, rerun algorithm audit, "
                "then rerun finite simulation diagnostics before promotion"
            ),
            "ok": True,
            "errors": [],
        }
        results_path = apply_dir / "algorithm_repair_sandbox_apply_results.jsonl"
        results_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
        (apply_dir / "algorithm_repair_sandbox_apply_manifest.json").write_text(
            json.dumps({"results_jsonl": str(results_path), "n_candidates": 1, "all_ok": True}),
            encoding="utf-8",
        )
        payload = rerun_algorithm_repair_sandbox_applications(
            apply_dir,
            Path("runs/test_algorithm_repair_sandbox_rerun"),
            question_file=Path("examples/research_questions.json"),
            n_runs=12,
            seed=20260530,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_candidates"], 1)
        self.assertEqual(payload["n_ok"], 1)
        rows = [
            json.loads(line)
            for line in Path(payload["results_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["evidence_kind"], "current_registry_rerun_with_guard_replay")
        self.assertTrue(rows[0]["registry_rerun_completed"])
        self.assertTrue(rows[0]["guard_plan_replayed"])
        self.assertFalse(rows[0]["production_patch_applied"])
        self.assertEqual(rows[0]["rerun_status"], "RERUN_EVIDENCE_READY")
        self.assertEqual(rows[0]["baseline_metrics"]["n_runs"], 12.0)
        self.assertIn("guard_failed_fraction", rows[0]["guarded_metrics"])
        self.assertIn("isolated code workspace", rows[0]["required_next_gate"])

    def test_algorithm_repair_sandbox_patch_eval_executes_isolated_patch(self) -> None:
        apply_dir = Path("runs/test_algorithm_repair_sandbox_patch_eval_input")
        apply_dir.mkdir(parents=True, exist_ok=True)
        result = {
            "application_id": "algorithm_repair_sandbox_apply:test",
            "candidate_id": "algorithm_repair_candidate:test",
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "patch_application_mode": "non_mutating_guard_plan",
            "patch_applied_to_production": False,
            "sandbox_artifact_created": True,
            "registry_audit_ok": True,
            "rerun_evidence_kind": "registry_audit_plus_guard_gate",
            "allowed_patch_scope": [
                "add finite-value metric guards",
                "record non-finite replicate diagnostics",
                "do not change estimand or theorem statement",
            ],
            "required_next_gate": (
                "apply bounded patch in isolated workspace, rerun algorithm audit, "
                "then rerun finite simulation diagnostics before promotion"
            ),
            "ok": True,
            "errors": [],
        }
        results_path = apply_dir / "algorithm_repair_sandbox_apply_results.jsonl"
        results_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
        (apply_dir / "algorithm_repair_sandbox_apply_manifest.json").write_text(
            json.dumps({"results_jsonl": str(results_path), "n_candidates": 1, "all_ok": True}),
            encoding="utf-8",
        )
        payload = evaluate_algorithm_repair_sandbox_patches(
            apply_dir,
            Path("runs/test_algorithm_repair_sandbox_patch_eval"),
            question_file=Path("examples/research_questions.json"),
            n_runs=12,
            seed=20260531,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_candidates"], 1)
        self.assertEqual(payload["n_ok"], 1)
        self.assertEqual(payload["n_isolated_patches_executed"], 1)
        self.assertEqual(payload["n_before_after_comparisons"], 1)
        self.assertEqual(payload["n_production_patches_applied"], 0)
        self.assertTrue(Path(payload["patch_module"]).exists())
        rows = [
            json.loads(line)
            for line in Path(payload["results_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(rows[0]["isolated_patch_executed"])
        self.assertTrue(rows[0]["before_after_comparison_ready"])
        self.assertFalse(rows[0]["production_patch_applied"])
        self.assertFalse(rows[0]["promotion_ready"])
        self.assertEqual(rows[0]["baseline_metrics"]["n_runs"], 12.0)
        self.assertEqual(rows[0]["patched_metrics"]["finite_guard_patch_applied"], 1.0)
        self.assertIn(
            rows[0]["comparison_status"],
            {
                "ISOLATED_PATCH_EXECUTED_NO_NUMERICAL_DELTA",
                "ISOLATED_PATCH_CHANGED_NUMERICAL_METRICS",
                "ISOLATED_PATCH_REMOVED_NONFINITE_METRICS",
            },
        )

    def test_algorithm_repair_patch_training_export_preserves_promotion_boundary(self) -> None:
        patch_eval_dir = Path("runs/test_algorithm_repair_patch_training_input")
        patch_eval_dir.mkdir(parents=True, exist_ok=True)
        result = {
            "patch_eval_id": "algorithm_repair_sandbox_patch_eval:test",
            "application_id": "algorithm_repair_sandbox_apply:test",
            "candidate_id": "algorithm_repair_candidate:test",
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "question_id": "q",
            "problem_class": "semiparametric_causal_ate",
            "patch_application_mode": "isolated_workspace_deterministic_finite_guard",
            "baseline_metrics": {"n_runs": 12.0, "coverage_95": 0.93},
            "patched_metrics": {
                "n_runs": 12.0,
                "coverage_95": 0.93,
                "finite_guard_patch_applied": 1.0,
            },
            "metric_deltas": {"coverage_95": 0.0},
            "nonfinite_baseline_metrics": [],
            "nonfinite_patched_metrics": [],
            "isolated_patch_executed": True,
            "before_after_comparison_ready": True,
            "production_patch_applied": False,
            "promotion_ready": False,
            "comparison_status": "ISOLATED_PATCH_EXECUTED_NO_NUMERICAL_DELTA",
            "required_next_gate": "reviewed source commit plus full release audit",
            "ok": True,
            "errors": [],
        }
        results_path = patch_eval_dir / "algorithm_repair_sandbox_patch_eval_results.jsonl"
        results_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
        (patch_eval_dir / "algorithm_repair_sandbox_patch_eval_manifest.json").write_text(
            json.dumps({"results_jsonl": str(results_path), "n_candidates": 1, "all_ok": True}),
            encoding="utf-8",
        )
        payload = export_algorithm_repair_patch_training_dataset(
            patch_eval_dir,
            Path("runs/test_algorithm_repair_patch_training_export"),
            validation_fraction=0.0,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_training_examples"], 1)
        self.assertEqual(payload["n_train"], 1)
        self.assertEqual(payload["n_validation"], 0)
        self.assertEqual(payload["n_production_patches_applied"], 0)
        rows = [
            json.loads(line)
            for line in Path(payload["train_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["task"], "algorithm_repair_patch_promotion_policy")
        completion = json.loads(rows[0]["completion"])
        self.assertEqual(completion["decision"], "hold_for_reviewed_production_commit")
        self.assertFalse(completion["production_patch_applied"])
        self.assertFalse(completion["promotion_ready"])
        self.assertIn("reviewed source commit", completion["required_next_gate"])

    def test_algorithm_repair_patch_policy_model_rejects_unsafe_promotion(self) -> None:
        training_dir = Path("runs/test_algorithm_repair_patch_policy_training_input")
        training_dir.mkdir(parents=True, exist_ok=True)
        example = {
            "schema_version": 1,
            "example_id": "algorithm_repair_patch_training:test",
            "split": "train",
            "task": "algorithm_repair_patch_promotion_policy",
            "prompt": "\n".join(
                [
                    "Patch evaluation context:",
                    json.dumps(
                        {
                            "algorithm_id": "oracle_aipw",
                            "target_procedure": "oracle_aipw_ate",
                            "comparison_status": "ISOLATED_PATCH_EXECUTED_NO_NUMERICAL_DELTA",
                            "production_patch_applied": False,
                            "promotion_ready": False,
                            "required_next_gate": "reviewed source commit plus full release audit",
                        },
                        sort_keys=True,
                    ),
                ]
            ),
            "completion": json.dumps(
                {
                    "decision": "hold_for_reviewed_production_commit",
                    "production_patch_applied": False,
                    "promotion_ready": False,
                    "required_next_gate": "reviewed source commit plus full release audit",
                },
                sort_keys=True,
            ),
            "patch_eval_id": "algorithm_repair_sandbox_patch_eval:test",
            "application_id": "algorithm_repair_sandbox_apply:test",
            "candidate_id": "algorithm_repair_candidate:test",
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "question_id": "q",
            "problem_class": "semiparametric_causal_ate",
            "comparison_status": "ISOLATED_PATCH_EXECUTED_NO_NUMERICAL_DELTA",
            "required_next_gate": "reviewed source commit plus full release audit",
            "production_patch_applied": False,
            "promotion_ready": False,
            "tags": ["algorithm_repair", "patch_eval", "oracle_aipw"],
        }
        train_path = training_dir / "algorithm_repair_patch_train.jsonl"
        validation_path = training_dir / "algorithm_repair_patch_validation.jsonl"
        train_path.write_text(json.dumps(example) + "\n", encoding="utf-8")
        validation_path.write_text(json.dumps({**example, "split": "validation"}) + "\n", encoding="utf-8")
        payload = train_algorithm_repair_patch_policy_model(
            train_path,
            Path("runs/test_algorithm_repair_patch_policy_model"),
            validation_jsonl=validation_path,
            epochs=40,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_train"], 1)
        self.assertEqual(payload["n_validation"], 1)
        self.assertEqual(payload["n_training_pairs"], 2)
        self.assertEqual(payload["validation_chose_gold"], 1)
        self.assertEqual(payload["validation_rejected_unsafe"], 1)
        self.assertGreater(payload["n_features"], 0)
        model = load_algorithm_repair_patch_policy_model(Path(payload["model_json"]))
        self.assertTrue(model.feature_names)
        rows = [
            json.loads(line)
            for line in Path(payload["validation_predictions_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["predicted_decision"], "hold_for_reviewed_production_commit")
        self.assertFalse(rows[0]["predicted_production_patch_applied"])
        self.assertFalse(rows[0]["predicted_promotion_ready"])

    def test_algorithm_repair_production_patch_plan_exports_reviewed_source_plan(self) -> None:
        model_dir = Path("runs/test_algorithm_repair_production_patch_plan_input")
        model_dir.mkdir(parents=True, exist_ok=True)
        example = {
            "example_id": "algorithm_repair_patch_training:test",
            "patch_eval_id": "algorithm_repair_sandbox_patch_eval:test",
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "comparison_status": "ISOLATED_PATCH_EXECUTED_NO_NUMERICAL_DELTA",
            "required_next_gate": "reviewed source commit plus full release audit",
            "prompt": "nonfinite finite_guard production_patch_applied false promotion_ready false",
            "completion": json.dumps(
                {
                    "decision": "hold_for_reviewed_production_commit",
                    "production_patch_applied": False,
                    "promotion_ready": False,
                    "required_next_gate": "reviewed source commit plus full release audit",
                },
                sort_keys=True,
            ),
        }
        prediction = {
            "example_id": example["example_id"],
            "split": "validation",
            "patch_eval_id": example["patch_eval_id"],
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "gold_completion": example["completion"],
            "predicted_completion": example["completion"],
            "unsafe_completion": "{}",
            "gold_score": 0.9,
            "unsafe_score": 0.1,
            "chose_gold": True,
            "rejected_unsafe": True,
            "predicted_valid_json": True,
            "predicted_decision": "hold_for_reviewed_production_commit",
            "predicted_production_patch_applied": False,
            "predicted_promotion_ready": False,
        }
        train_path = model_dir / "algorithm_repair_patch_train.jsonl"
        validation_path = model_dir / "algorithm_repair_patch_validation.jsonl"
        train_predictions_path = model_dir / "algorithm_repair_patch_policy_train_predictions.jsonl"
        validation_predictions_path = model_dir / "algorithm_repair_patch_policy_validation_predictions.jsonl"
        train_path.write_text(json.dumps(example) + "\n", encoding="utf-8")
        validation_path.write_text(json.dumps(example) + "\n", encoding="utf-8")
        train_predictions_path.write_text(json.dumps(prediction) + "\n", encoding="utf-8")
        validation_predictions_path.write_text(json.dumps(prediction) + "\n", encoding="utf-8")
        (model_dir / "algorithm_repair_patch_policy_model_manifest.json").write_text(
            json.dumps(
                {
                    "all_ok": True,
                    "train_jsonl": str(train_path),
                    "validation_jsonl": str(validation_path),
                    "train_predictions_jsonl": str(train_predictions_path),
                    "validation_predictions_jsonl": str(validation_predictions_path),
                }
            ),
            encoding="utf-8",
        )
        payload = export_algorithm_repair_production_patch_plan(
            model_dir,
            Path("runs/test_algorithm_repair_production_patch_plan"),
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_plans"], 1)
        self.assertEqual(payload["n_ok"], 1)
        self.assertEqual(payload["n_review_required"], 1)
        self.assertEqual(payload["n_production_patches_applied"], 0)
        rows = [
            json.loads(line)
            for line in Path(payload["plans_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["source_file"], "ai_statistician/research_lab.py")
        self.assertEqual(rows[0]["target_symbol"], "ResearchSimulator._oracle_aipw")
        self.assertEqual(rows[0]["patch_kind"], "finite_metric_guard")
        self.assertTrue(rows[0]["review_required"])
        self.assertFalse(rows[0]["production_patch_applied"])
        self.assertIn("full research-system audit", " ".join(rows[0]["release_gates"]))

    def test_algorithm_repair_reviewed_patch_apply_writes_isolated_source_diff(self) -> None:
        plan_dir = Path("runs/test_algorithm_repair_reviewed_patch_apply_input")
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan = {
            "plan_id": "algorithm_repair_production_patch_plan:test",
            "example_id": "algorithm_repair_patch_training:test",
            "patch_eval_id": "algorithm_repair_sandbox_patch_eval:test",
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "source_file": "ai_statistician/research_lab.py",
            "target_symbol": "ResearchSimulator._oracle_aipw",
            "patch_kind": "finite_metric_guard",
            "patch_summary": "Port the isolated finite-metric guard.",
            "predicted_decision": "hold_for_reviewed_production_commit",
            "comparison_status": "ISOLATED_PATCH_EXECUTED_NO_NUMERICAL_DELTA",
            "gold_score": 0.9,
            "unsafe_score": 0.1,
            "review_required": True,
            "production_patch_applied": False,
            "promotion_ready": False,
            "required_source_edits": ["Add finite-value metric validation."],
            "release_gates": ["rerun full research-system audit before promotion"],
            "ok": True,
            "errors": [],
        }
        plans_path = plan_dir / "algorithm_repair_production_patch_plans.jsonl"
        plans_path.write_text(json.dumps(plan) + "\n", encoding="utf-8")
        (plan_dir / "algorithm_repair_production_patch_plan_manifest.json").write_text(
            json.dumps({"plans_jsonl": str(plans_path), "n_plans": 1, "all_ok": True}),
            encoding="utf-8",
        )
        payload = apply_reviewed_algorithm_repair_source_patches(
            plan_dir,
            Path("runs/test_algorithm_repair_reviewed_patch_apply"),
            source_root=Path("."),
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_plans"], 1)
        self.assertEqual(payload["n_ok"], 1)
        self.assertEqual(payload["n_source_changed"], 1)
        self.assertEqual(payload["n_syntax_valid"], 1)
        self.assertEqual(payload["n_target_symbol_found"], 1)
        self.assertEqual(payload["n_production_patches_applied"], 0)
        rows = [
            json.loads(line)
            for line in Path(payload["results_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(rows[0]["source_changed"])
        self.assertTrue(rows[0]["syntax_valid"])
        self.assertFalse(rows[0]["production_patch_applied"])
        patched_text = Path(rows[0]["patched_source_file"]).read_text(encoding="utf-8")
        diff_text = Path(rows[0]["diff_file"]).read_text(encoding="utf-8")
        self.assertIn("finite_guard_patch_applied", patched_text)
        self.assertIn("finite_guard_patch_applied", diff_text)
        self.assertNotIn("finite_guard_patch_applied", Path("ai_statistician/research_lab.py").read_text(encoding="utf-8"))

    def test_algorithm_repair_reviewed_patch_validate_imports_copied_patch(self) -> None:
        plan_dir = Path("runs/test_algorithm_repair_reviewed_patch_validate_input")
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan = {
            "plan_id": "algorithm_repair_production_patch_plan:test",
            "example_id": "algorithm_repair_patch_training:test",
            "patch_eval_id": "algorithm_repair_sandbox_patch_eval:test",
            "algorithm_id": "oracle_aipw",
            "target_procedure": "oracle_aipw_ate",
            "source_file": "ai_statistician/research_lab.py",
            "target_symbol": "ResearchSimulator._oracle_aipw",
            "patch_kind": "finite_metric_guard",
            "patch_summary": "Port the isolated finite-metric guard.",
            "predicted_decision": "hold_for_reviewed_production_commit",
            "comparison_status": "ISOLATED_PATCH_EXECUTED_NO_NUMERICAL_DELTA",
            "gold_score": 0.9,
            "unsafe_score": 0.1,
            "review_required": True,
            "production_patch_applied": False,
            "promotion_ready": False,
            "required_source_edits": ["Add finite-value metric validation."],
            "release_gates": ["rerun full research-system audit before promotion"],
            "ok": True,
            "errors": [],
        }
        plans_path = plan_dir / "algorithm_repair_production_patch_plans.jsonl"
        plans_path.write_text(json.dumps(plan) + "\n", encoding="utf-8")
        (plan_dir / "algorithm_repair_production_patch_plan_manifest.json").write_text(
            json.dumps({"plans_jsonl": str(plans_path), "n_plans": 1, "all_ok": True}),
            encoding="utf-8",
        )
        apply_payload = apply_reviewed_algorithm_repair_source_patches(
            plan_dir,
            Path("runs/test_algorithm_repair_reviewed_patch_validate_apply"),
            source_root=Path("."),
        )
        self.assertTrue(apply_payload["all_ok"])
        payload = validate_reviewed_algorithm_repair_patches(
            Path("runs/test_algorithm_repair_reviewed_patch_validate_apply"),
            Path("runs/test_algorithm_repair_reviewed_patch_validate"),
            source_root=Path("."),
            question_file=Path("examples/research_questions.json"),
            n_runs=5,
            seed=20260601,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_candidates"], 1)
        self.assertEqual(payload["n_ok"], 1)
        self.assertEqual(payload["n_import_ok"], 1)
        self.assertEqual(payload["n_algorithm_audit_ok"], 1)
        self.assertEqual(payload["n_simulation_completed"], 1)
        self.assertEqual(payload["n_patched_metric_present"], 1)
        self.assertEqual(payload["n_finite_metrics_ok"], 1)
        rows = [
            json.loads(line)
            for line in Path(payload["results_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(rows[0]["import_ok"])
        self.assertTrue(rows[0]["patched_metric_present"])
        self.assertEqual(rows[0]["metrics"]["finite_guard_patch_applied"], 1.0)
        self.assertFalse(rows[0]["production_patch_applied"])

    def test_research_loop_default_proof_engineer_bridges_formal_gap(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        procedure, theorem_goal = TheoryPlanner().plan(problem)
        gap = FormalSubclaim(
            id="gap:aipw_double_robustness",
            title="AIPW double robustness conditional residual bridge",
            status="FORMAL_GAP",
            claim="conditional mean residual zero should cancel AIPW augmentation terms",
            claim_type="theory_gap",
            gap_reason="conditional_mean_residual_zero is not fully formalized",
            lean_statement="-- FORMAL_GAP conditional_mean_residual_zero",
        )
        report = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[gap],
            simulations=[],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "formal_gap:gap:aipw_double_robustness",
                            "owner_agent": "formal_verifier",
                            "trigger": "FORMAL_GAP",
                            "priority": "high",
                            "action": "retrieve_or_build_missing_lean_primitives",
                            "evidence": "conditional_mean_residual_zero is needed",
                            "required_primitives": ["conditional_mean_residual_zero"],
                            "target_theorem_goal": "aipw_double_robustness",
                        }
                    ]
                }
            },
            status="RESEARCH_TRACE_READY_WITH_FORMAL_GAPS",
        )

        second = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[gap],
            simulations=[],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "monitor:proof_bridge",
                            "owner_agent": "research_coordinator",
                            "trigger": "NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
                            "action": "archive_trace_or_expand_benchmark_stress_tests",
                            "evidence": "proof bridge revision was available for the next round",
                        }
                    ]
                }
            },
            status="RESEARCH_TRACE_READY_WITH_FORMAL_GAPS",
        )
        reports = [report, second]

        class FakeLab:
            def __init__(self, report):
                self.report = report

            async def run(self, question):
                return self.report

        class KernelVerifiedMockProofVerifier(MockProofVerifier):
            async def verify(self, obligation, proof_body, retrieval_hits):
                check = await super().verify(obligation, proof_body, retrieval_hits)
                return ProofCheck(
                    obligation_id=check.obligation_id,
                    ok=check.ok,
                    proof_body=check.proof_body,
                    verifier="kernel-verified-mock",
                    verification_strength="mock_kernel_verified_for_loop_routing",
                    kernel_verified=check.ok,
                    elapsed_ms=check.elapsed_ms,
                    errors=check.errors,
                    retrieval_hits=check.retrieval_hits,
                )

        result = asyncio.run(
            ResearchLoopCoordinator(
                proof_verifier=KernelVerifiedMockProofVerifier(),
                n_runs=25,
                seed=17,
                lab_factory=lambda _n, _s: FakeLab(reports.pop(0)),
            ).iterate(
                question,
                max_rounds=2,
            )
        )
        self.assertEqual(result["status"], "CONVERGED_MONITOR_READY")
        self.assertEqual(result["n_theory_revisions"], 1)
        self.assertTrue(result["honesty_boundary"]["executes_default_proof_engineer_bridge_handler"])
        action = result["rounds"][0]["actions"][0]
        self.assertEqual(action["execution_status"], "EXECUTED_PROOF_BANK_BRIDGE_REPAIR")
        self.assertTrue(action["repair_contract_ok"])
        self.assertEqual(
            action["repair_artifact"]["proof_obligation_id"],
            "conditional_mean_residual_zero_of_condExp_ae_eq",
        )
        self.assertIn("lean_statement", action["repair_artifact"])
        self.assertEqual(
            action["repair_artifact"]["selected_bridge_obligation_id"],
            action["repair_artifact"]["proof_obligation_id"],
        )
        self.assertTrue(action["repair_artifact"]["ranked_bridge_obligations"])
        self.assertTrue(action["repair_artifact"]["bridge_chain_order"])
        self.assertTrue(action["repair_artifact"]["bridge_chain"])
        self.assertTrue(action["repair_artifact"]["remaining_frontier_interface"])
        self.assertIn("not a proof of the full frontier theorem", action["repair_artifact"]["proof_evidence_boundary"])
        self.assertTrue(action["rerun_requested"])
        self.assertEqual(action["repair_task"]["task_type"], "proof_bank_expansion_from_formal_gap")
        bridge_revision = result["theory_revisions"][0]["repair_artifact"]
        self.assertEqual(bridge_revision["revision_kind"], "proof_bridge_integration")
        self.assertFalse(bridge_revision["full_theorem_proved"])
        self.assertEqual(result["rounds"][1]["actions"][0]["execution_status"], "EXECUTED_MONITOR")

    def test_research_loop_default_proof_engineer_repairs_failed_registered_obligation(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        problem = ProblemFormalizer().formalize(question)
        procedure, theorem_goal = TheoryPlanner().plan(problem)
        obligation = get_obligation("prob_measure_univ")
        failed = FormalSubclaim(
            id=f"{question.id}:{obligation.id}",
            title=obligation.title,
            status="FAILED",
            claim=obligation.english,
            claim_type="lean_obligation",
            proof_obligation_id=obligation.id,
            lean_statement=obligation.formal_statement,
            formalization_status="verification_failed",
            verifier="test-verifier",
            verification_strength="test_failed_first_attempt",
            kernel_verified=False,
            errors=["test simulates stale failed proof body"],
            proof_dependencies=obligation.expected_lemmas,
        )
        first = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[failed],
            simulations=[],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": f"failed_obligation:{obligation.id}",
                            "owner_agent": "formal_verifier",
                            "trigger": "FAILED_PROOF_OBLIGATION",
                            "priority": "high",
                            "action": "repair_axiom_verified_proof_or_downgrade_to_gap",
                            "evidence": "test simulates stale failed proof body",
                            "required_primitives": list(obligation.expected_lemmas),
                            "target_theorem_goal": obligation.id,
                        }
                    ]
                }
            },
            status="FORMAL_BLOCKED",
        )
        second = ResearchReport(
            question=question,
            problem=problem,
            procedures=procedure,
            knowledge=[],
            paper_sources=[],
            formal_subclaims=[],
            simulations=[],
            theorem_goals=theorem_goal,
            theory_plan={
                "next_iteration_agenda": {
                    "items": [
                        {
                            "id": "monitor:failed-proof-repaired",
                            "owner_agent": "research_coordinator",
                            "trigger": "NO_BLOCKING_GAPS_OR_FAILED_SIMULATIONS",
                            "action": "archive_trace_or_expand_benchmark_stress_tests",
                            "evidence": "registered proof obligation repair was available for the next round",
                        }
                    ]
                }
            },
            status="RESEARCH_TRACE_READY_WITH_FORMAL_GAPS",
        )
        reports = [first, second]

        class FakeLab:
            def __init__(self, report):
                self.report = report

            async def run(self, question):
                return self.report

        class KernelVerifiedMockProofVerifier(MockProofVerifier):
            async def verify(self, obligation, proof_body, retrieval_hits):
                check = await super().verify(obligation, proof_body, retrieval_hits)
                return ProofCheck(
                    obligation_id=check.obligation_id,
                    ok=check.ok,
                    proof_body=check.proof_body,
                    verifier="kernel-verified-mock",
                    verification_strength="mock_kernel_verified_for_failed_obligation_repair",
                    kernel_verified=check.ok,
                    elapsed_ms=check.elapsed_ms,
                    errors=check.errors,
                    retrieval_hits=check.retrieval_hits,
                )

        result = asyncio.run(
            ResearchLoopCoordinator(
                proof_verifier=KernelVerifiedMockProofVerifier(),
                n_runs=10,
                seed=20260601,
                lab_factory=lambda _n, _s: FakeLab(reports.pop(0)),
            ).iterate(
                question,
                max_rounds=2,
            )
        )
        self.assertEqual(result["status"], "CONVERGED_MONITOR_READY")
        action = result["rounds"][0]["actions"][0]
        self.assertEqual(action["execution_status"], "EXECUTED_FAILED_PROOF_OBLIGATION_REPAIR")
        self.assertTrue(action["repair_contract_ok"])
        self.assertTrue(action["rerun_requested"])
        self.assertEqual(action["live_repair_handler"], "DefaultProofEngineer")
        self.assertEqual(action["live_repair_task_type"], "lean_proof_repair_from_axle_error")
        artifact = action["repair_artifact"]
        self.assertEqual(artifact["proof_obligation_id"], "prob_measure_univ")
        self.assertEqual(artifact["repaired_proof_body"], obligation.proof_body)
        self.assertTrue(artifact["kernel_verified"])
        self.assertIn("repaired_proof_body", artifact)
        self.assertIn("error_analysis", artifact)
        self.assertIn("proof_dependencies", artifact)
        self.assertEqual(action["repair_task"]["task_type"], "lean_proof_repair_from_axle_error")
        self.assertEqual(result["rounds"][1]["actions"][0]["execution_status"], "EXECUTED_MONITOR")

    def test_proof_bridge_revision_overlay_updates_existing_theorem_goal(self) -> None:
        question = load_open_research_questions(Path("examples/research_questions.json"))[0]
        revision = {
            "artifact_id": "theory_revision:proof_bridge:test",
            "target_procedure": "oracle_aipw_ate",
            "repair_artifact": {
                "revision_kind": "proof_bridge_integration",
                "target_procedure": "oracle_aipw_ate",
                "target_theorem_goal": "aipw_double_robustness",
                "proof_obligation_id": "aipw_score_expectation_target_of_zero_aug",
                "bridge_for_primitives": ["conditional_mean_residual_zero"],
                "full_theorem_proved": False,
            },
        }

        async def run():
            return await AIStatisticalTheoryLab(
                proof_verifier=MockProofVerifier(),
                n_runs=10,
                seed=20260531,
                theory_revisions=[revision],
            ).run(question)

        report = asyncio.run(run())
        applied = report.theory_plan["applied_theory_revisions"]
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0]["revision_kind"], "proof_bridge_integration")
        self.assertFalse(applied[0]["full_theorem_proved"])
        self.assertTrue(applied[0]["algorithm_unchanged"])
        procedure_row = report.theory_plan["candidate_procedures"][0]
        self.assertEqual(procedure_row["id"], "oracle_aipw_ate")
        self.assertEqual(procedure_row["algorithm"], "oracle_aipw")
        roadmap = {row["id"]: row for row in report.theory_plan["theorem_roadmap"]}
        self.assertIn("aipw_double_robustness", roadmap)
        self.assertIn(
            "aipw_score_expectation_target_of_zero_aug",
            roadmap["aipw_double_robustness"]["proof_obligations"],
        )

    def test_research_loop_benchmark_exports_live_repair_artifacts(self) -> None:
        async def run():
            questions = load_open_research_questions(Path("examples/research_questions.json"))[:1]
            return await run_research_loop_benchmark(
                questions,
                Path("runs/test_research_loop_live_repair_artifacts"),
                proof_verifier=MockProofVerifier(),
                config=LoopConfig(max_rounds=2, n_runs=25, seed=20260528),
            )

        from ai_statistician.research_loop import LoopConfig, run_research_loop_benchmark

        payload = asyncio.run(run())
        self.assertTrue(payload["all_loop_traces_written"])
        self.assertTrue(payload["all_repair_tasks_exported"])
        self.assertTrue(payload["all_live_repair_artifacts_exported"])
        self.assertGreater(payload["n_live_repair_artifacts"], 0)
        self.assertEqual(
            payload["live_repair_artifacts_contract_ok"],
            payload["n_live_repair_artifacts"],
        )
        self.assertIn("DefaultProofEngineer", payload["live_repair_artifacts_by_handler"])
        artifact_path = Path(payload["live_repair_artifacts_jsonl"])
        self.assertTrue(artifact_path.exists())
        rows = [json.loads(line) for line in artifact_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), payload["n_live_repair_artifacts"])
        self.assertTrue(rows[0]["repair_contract_ok"])
        self.assertIn("repair_artifact", rows[0])
        self.assertIn("proof_obligation_id", rows[0]["repair_artifact"])

    def test_research_loop_repair_audit_exports_sft_examples(self) -> None:
        loop_dir = Path("runs/test_research_loop_repair_audit_input")
        loop_dir.mkdir(parents=True, exist_ok=True)
        task_path = loop_dir / "research_loop_repair_tasks.jsonl"
        task = {
            "schema_version": 1,
            "task_id": "loop_repair:theory_developer:theory_revision_from_simulation_failure:test",
            "source_action_id": "simulation:test",
            "question_id": "q",
            "problem_class": "semiparametric_causal_ate",
            "owner_agent": "theory_developer",
            "task_type": "theory_revision_from_simulation_failure",
            "trigger": "THEORY_OR_PROCEDURE_ISSUE",
            "priority": "high",
            "prompt": "Revise the theory plan.",
            "evidence": "coverage below threshold",
            "context": {
                "dgp": "iid observations",
                "estimand": "ATE",
                "assumptions": ["iid"],
                "asymptotic_regime": "sqrt(n)",
            },
            "acceptance_criteria": ["simulation diagnostics pass after revision"],
            "output_contract": {
                "required_fields": [
                    "revised_procedure",
                    "revised_theorem_goals",
                    "assumption_delta",
                    "expected_simulation_delta",
                ],
                "required_gate": "rerun research-loop without same diagnosis",
            },
        }
        task_path.write_text(json.dumps(task) + "\n", encoding="utf-8")
        (loop_dir / "research_loop_manifest.json").write_text(
            json.dumps({"repair_tasks_jsonl": str(task_path), "n_repair_tasks": 1}),
            encoding="utf-8",
        )
        payload = audit_research_loop_repair_tasks(
            loop_dir,
            Path("runs/test_research_loop_repair_audit"),
            validation_fraction=0.0,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_tasks"], 1)
        self.assertEqual(payload["n_sft_examples"], 1)
        self.assertEqual(payload["by_owner"]["theory_developer"], 1)
        self.assertTrue(Path(payload["train_jsonl"]).exists())
        rows = [
            json.loads(line)
            for line in Path(payload["train_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["task"], "research_loop_repair_planning")
        self.assertIn("theory_revision_from_simulation_failure", rows[0]["tags"])

    def test_research_loop_live_repair_audit_exports_sft_examples(self) -> None:
        loop_dir = Path("runs/test_research_loop_live_repair_audit_input")
        loop_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = loop_dir / "research_loop_live_repair_artifacts.jsonl"
        required_fields = [
            "lean_statement",
            "proof_body",
            "expected_lemmas",
            "proof_dependencies",
            "reuse_targets",
            "proof_obligation_id",
            "kernel_verified",
            "verification_strength",
        ]
        artifact = {
            "schema_version": 1,
            "artifact_id": "live_repair:test",
            "question_id": "q",
            "round": 1,
            "source_action_id": "formal_gap:test",
            "owner_agent": "formal_verifier",
            "trigger": "FORMAL_GAP",
            "execution_status": "EXECUTED_PROOF_BANK_BRIDGE_REPAIR",
            "task_type": "proof_bank_expansion_from_formal_gap",
            "live_repair_handler": "DefaultProofEngineer",
            "repair_contract_ok": True,
            "repair_contract_errors": [],
            "rerun_requested": False,
            "repair_artifact": {
                "lean_statement": "theorem test_live_repair : True := by sorry",
                "proof_body": "by trivial",
                "expected_lemmas": ["trivial"],
                "proof_dependencies": ["trivial"],
                "reuse_targets": ["test_goal"],
                "proof_obligation_id": "test_live_repair",
                "kernel_verified": True,
                "verification_strength": "axle_lean_kernel",
            },
            "repair_contract": {
                "required_fields": required_fields,
                "required_gate": "AXLE verify_proof kernel_verified=true",
            },
        }
        artifact_path.write_text(json.dumps(artifact) + "\n", encoding="utf-8")
        (loop_dir / "research_loop_manifest.json").write_text(
            json.dumps(
                {
                    "live_repair_artifacts_jsonl": str(artifact_path),
                    "n_live_repair_artifacts": 1,
                }
            ),
            encoding="utf-8",
        )
        payload = audit_research_loop_live_repair_artifacts(
            loop_dir,
            Path("runs/test_research_loop_live_repair_audit"),
            validation_fraction=0.0,
        )
        self.assertTrue(payload["all_ok"])
        self.assertEqual(payload["n_artifacts"], 1)
        self.assertEqual(payload["n_ok"], 1)
        self.assertEqual(payload["n_kernel_verified"], 1)
        self.assertEqual(payload["n_sft_examples"], 1)
        self.assertEqual(payload["by_handler"]["DefaultProofEngineer"], 1)
        self.assertTrue(Path(payload["train_jsonl"]).exists())
        rows = [
            json.loads(line)
            for line in Path(payload["train_jsonl"]).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(rows[0]["task"], "research_loop_live_repair_execution")
        completion = json.loads(rows[0]["completion"])
        self.assertEqual(completion["repair_artifact"]["proof_obligation_id"], "test_live_repair")
        self.assertIn("proof_bank_expansion_from_formal_gap", rows[0]["tags"])

    def test_prover_component_audit_is_honest_about_training_gaps(self) -> None:
        payload = build_prover_component_audit(root=Path("."))
        self.assertTrue(payload["paper_outline_exists"])
        self.assertFalse(payload["summary"]["honest_goal_complete"])
        statuses = {row["component"]: row["status"] for row in payload["rows"]}
        self.assertEqual(statuses["hard verifier / Lean kernel interface"], "READY")
        self.assertIn("PARTIAL", statuses["premise retrieval / Lean RAG / formal-source search"])
        self.assertEqual(statuses["tactic / whole-proof policy model"], "PARTIAL_WHOLE_PROOF_POLICY_TRAINER")
        self.assertEqual(statuses["model training pipeline"], "PARTIAL_BASELINE_TRAINER")
        self.assertFalse(payload["summary"]["honest_goal_complete"])
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
        self.assertTrue(payload["gates"]["architecture_audit"])
        self.assertTrue(payload["gates"]["research_capability_audit"])
        self.assertTrue(payload["gates"]["frontier_smoke_benchmark"])
        self.assertTrue(payload["gates"]["research_intake_audit"])
        self.assertTrue(payload["gates"]["adversarial_intake_audit"])
        self.assertTrue(payload["gates"]["research_knowledge_audit"])
        self.assertTrue(payload["gates"]["retrieval_audit"])
        self.assertTrue(payload["gates"]["formal_source_graph"])
        self.assertTrue(payload["gates"]["formal_source_retrieval_benchmark"])
        self.assertTrue(payload["gates"]["formal_source_retrieval_ablation"])
        self.assertTrue(payload["gates"]["fresh_holdout_frontier_audit"])
        self.assertTrue(payload["gates"]["research_algorithm_audit"])
        self.assertTrue(payload["gates"]["algorithm_simulation_stress_audit"])
        self.assertTrue(payload["gates"]["proof_audit"])
        self.assertTrue(payload["gates"]["proof_training_export"])
        self.assertTrue(payload["gates"]["proof_repair_export"])
        self.assertTrue(payload["gates"]["proof_policy_baseline"])
        self.assertTrue(payload["gates"]["proof_search_retrieval_ablation"])
        self.assertTrue(payload["gates"]["prover_component_audit"])
        self.assertTrue(payload["gates"]["research_benchmark"])
        self.assertTrue(payload["gates"]["formal_gap_skeletons"])
        self.assertTrue(payload["gates"]["research_trace_audit"])
        self.assertTrue(payload["gates"]["research_gap_backlog"])
        self.assertTrue(payload["gates"]["formalization_target_audit"])
        self.assertTrue(payload["gates"]["formal_gap_task_export"])
        self.assertTrue(payload["gates"]["autoform_target_export"])
        self.assertTrue(payload["gates"]["proof_bank_expansion_export"])
        self.assertTrue(payload["gates"]["primitive_source_coverage_audit"])
        self.assertTrue(payload["gates"]["research_training_export"])
        self.assertTrue(payload["gates"]["research_policy_baseline"])
        self.assertTrue(payload["gates"]["next_iteration_queue"])
        self.assertTrue(payload["gates"]["research_report"])
        self.assertTrue(payload["gates"]["research_loop"])
        self.assertTrue(payload["gates"]["research_loop_repair_audit"])
        self.assertTrue(payload["gates"]["research_loop_live_repair_audit"])
        self.assertTrue(payload["gates"]["algorithm_repair_promotion"])
        self.assertTrue(payload["gates"]["algorithm_repair_sandbox"])
        self.assertTrue(payload["gates"]["algorithm_repair_sandbox_apply"])
        self.assertTrue(payload["gates"]["algorithm_repair_sandbox_rerun"])
        self.assertTrue(payload["gates"]["algorithm_repair_sandbox_patch_eval"])
        self.assertTrue(payload["gates"]["algorithm_repair_patch_training_export"])
        self.assertTrue(payload["gates"]["algorithm_repair_patch_policy_model"])
        self.assertTrue(payload["gates"]["algorithm_repair_production_patch_plan"])
        self.assertTrue(payload["gates"]["algorithm_repair_reviewed_patch_apply"])
        self.assertTrue(payload["gates"]["algorithm_repair_reviewed_patch_validate"])
        self.assertTrue(payload["gates"]["evaluation_benchmark_guidance"])
        self.assertEqual(payload["counts"]["questions"], 10)
        self.assertEqual(payload["counts"]["frontier_questions"], 60)
        self.assertEqual(payload["counts"]["frontier_supported"], 60)
        self.assertEqual(payload["counts"]["frontier_unsupported"], 0)
        self.assertEqual(payload["counts"]["frontier_precision_ok"], payload["counts"]["frontier_precision_supported"])
        self.assertEqual(payload["counts"]["frontier_precision_flagged"], 0)
        self.assertEqual(payload["counts"]["frontier_backlog_ok"], payload["counts"]["frontier_backlog_total"])
        self.assertEqual(payload["counts"]["frontier_backlog_total"], payload["counts"]["frontier_unsupported"])
        self.assertEqual(payload["counts"]["frontier_backlog_domains"], 0)
        self.assertEqual(payload["counts"]["frontier_backlog_required_primitives"], 0)
        self.assertTrue(payload["counts"]["architecture_has_live_revision_loop"])
        self.assertGreaterEqual(payload["counts"]["architecture_components_partial"], 1)
        self.assertGreaterEqual(payload["counts"]["architecture_feedback_routes"], 5)
        self.assertFalse(payload["counts"]["research_capability_goal_complete"])
        self.assertEqual(
            payload["counts"]["research_capability_current_release_gate_met"],
            payload["counts"]["research_capability_current_release_gate"],
        )
        self.assertGreaterEqual(payload["counts"]["research_capability_partial"], 2)
        self.assertGreaterEqual(payload["counts"]["research_capability_not_achieved"], 1)
        self.assertGreaterEqual(payload["counts"]["frontier_smoke_questions"], 3)
        self.assertEqual(payload["counts"]["frontier_smoke_ready"], payload["counts"]["frontier_smoke_questions"])
        self.assertEqual(payload["counts"]["frontier_smoke_runs"], 25)
        self.assertGreater(payload["counts"]["frontier_smoke_total_elapsed_ms"], 0)
        self.assertTrue(payload["counts"]["frontier_smoke_slowest_stage"])
        self.assertGreater(payload["counts"]["frontier_smoke_slowest_stage_elapsed_ms"], 0)
        self.assertTrue(payload["counts"]["frontier_smoke_cache_enabled"])
        self.assertIn(payload["counts"]["frontier_smoke_cache_status"], {"hit", "miss"})
        self.assertTrue(payload["counts"]["frontier_smoke_cache_key"])
        self.assertTrue(payload["counts"]["research_benchmark_cache_enabled"])
        self.assertIn(payload["counts"]["research_benchmark_cache_status"], {"hit", "miss"})
        self.assertTrue(payload["counts"]["research_benchmark_cache_key"])
        self.assertEqual(payload["counts"]["research_loop_questions"], 1)
        self.assertTrue(payload["counts"]["research_loop_traces_written"])
        loop_manifest = json.loads(Path(payload["artifacts"]["research_loop"]).read_text())
        self.assertTrue(loop_manifest["formal_source_retriever_reused"])
        self.assertTrue(payload["counts"]["research_loop_repair_tasks_exported"])
        self.assertGreaterEqual(payload["counts"]["research_loop_repair_tasks"], 1)
        self.assertTrue(payload["counts"]["research_loop_live_repair_artifacts_exported"])
        self.assertGreaterEqual(payload["counts"]["research_loop_live_repair_artifacts"], 1)
        self.assertEqual(
            payload["counts"]["research_loop_live_repair_artifacts_contract_ok"],
            payload["counts"]["research_loop_live_repair_artifacts"],
        )
        self.assertEqual(
            payload["counts"]["research_loop_repair_tasks_ok"],
            payload["counts"]["research_loop_repair_tasks"],
        )
        self.assertGreaterEqual(payload["counts"]["research_loop_repair_sft_examples"], 1)
        self.assertEqual(
            payload["counts"]["research_loop_live_repair_artifacts_ok"],
            payload["counts"]["research_loop_live_repair_artifacts"],
        )
        self.assertGreaterEqual(payload["counts"]["research_loop_live_repair_sft_examples"], 1)
        self.assertEqual(
            payload["counts"]["algorithm_repair_promotion_candidates_ok"],
            payload["counts"]["algorithm_repair_promotion_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_sandbox_candidates_ok"],
            payload["counts"]["algorithm_repair_sandbox_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_sandbox_apply_candidates_ok"],
            payload["counts"]["algorithm_repair_sandbox_apply_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_sandbox_rerun_candidates_ok"],
            payload["counts"]["algorithm_repair_sandbox_rerun_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_sandbox_patch_eval_candidates_ok"],
            payload["counts"]["algorithm_repair_sandbox_patch_eval_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_sandbox_patch_eval_executed"],
            payload["counts"]["algorithm_repair_sandbox_patch_eval_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_sandbox_patch_eval_before_after"],
            payload["counts"]["algorithm_repair_sandbox_patch_eval_candidates"],
        )
        self.assertEqual(payload["counts"]["algorithm_repair_sandbox_patch_eval_production_patches"], 0)
        self.assertEqual(payload["counts"]["algorithm_repair_sandbox_patch_eval_promotion_ready"], 0)
        self.assertEqual(
            payload["counts"]["algorithm_repair_patch_training_examples"],
            payload["counts"]["algorithm_repair_sandbox_patch_eval_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_patch_training_train"]
            + payload["counts"]["algorithm_repair_patch_training_validation"],
            payload["counts"]["algorithm_repair_patch_training_examples"],
        )
        self.assertEqual(payload["counts"]["algorithm_repair_patch_training_production_patches"], 0)
        self.assertEqual(payload["counts"]["algorithm_repair_patch_training_promotion_ready"], 0)
        self.assertEqual(
            payload["counts"]["algorithm_repair_patch_policy_train"],
            payload["counts"]["algorithm_repair_patch_training_train"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_patch_policy_validation"],
            payload["counts"]["algorithm_repair_patch_training_validation"],
        )
        self.assertGreater(payload["counts"]["algorithm_repair_patch_policy_features"], 0)
        self.assertGreaterEqual(payload["counts"]["algorithm_repair_patch_policy_training_pairs"], 0)
        self.assertGreaterEqual(
            payload["counts"]["algorithm_repair_patch_policy_validation_safe_decision_accuracy"],
            0.0,
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_production_patch_plans_ok"],
            payload["counts"]["algorithm_repair_production_patch_plans"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_production_patch_review_required"],
            payload["counts"]["algorithm_repair_production_patch_plans"],
        )
        self.assertEqual(payload["counts"]["algorithm_repair_production_patch_applied"], 0)
        self.assertEqual(payload["counts"]["algorithm_repair_production_patch_promotion_ready"], 0)
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_apply_candidates_ok"],
            payload["counts"]["algorithm_repair_reviewed_patch_apply_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_apply_source_changed"],
            payload["counts"]["algorithm_repair_reviewed_patch_apply_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_apply_syntax_valid"],
            payload["counts"]["algorithm_repair_reviewed_patch_apply_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_apply_target_found"],
            payload["counts"]["algorithm_repair_reviewed_patch_apply_candidates"],
        )
        self.assertEqual(payload["counts"]["algorithm_repair_reviewed_patch_apply_production_patches"], 0)
        self.assertEqual(payload["counts"]["algorithm_repair_reviewed_patch_apply_promotion_ready"], 0)
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_validate_candidates_ok"],
            payload["counts"]["algorithm_repair_reviewed_patch_validate_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_validate_import_ok"],
            payload["counts"]["algorithm_repair_reviewed_patch_validate_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_validate_algorithm_audit_ok"],
            payload["counts"]["algorithm_repair_reviewed_patch_validate_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_validate_simulation_completed"],
            payload["counts"]["algorithm_repair_reviewed_patch_validate_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_validate_patched_metric_present"],
            payload["counts"]["algorithm_repair_reviewed_patch_validate_candidates"],
        )
        self.assertEqual(
            payload["counts"]["algorithm_repair_reviewed_patch_validate_finite_metrics_ok"],
            payload["counts"]["algorithm_repair_reviewed_patch_validate_candidates"],
        )
        self.assertEqual(payload["counts"]["algorithm_repair_reviewed_patch_validate_production_patches"], 0)
        self.assertEqual(payload["counts"]["algorithm_repair_reviewed_patch_validate_promotion_ready"], 0)
        self.assertEqual(payload["counts"]["evaluation_benchmark_guidance_suites"], 10)
        self.assertGreaterEqual(payload["counts"]["evaluation_benchmark_guidance_exercised"], 8)
        self.assertGreaterEqual(payload["counts"]["evaluation_benchmark_guidance_stale_or_missing"], 0)
        self.assertGreaterEqual(payload["counts"]["evaluation_benchmark_guidance_capacity_gaps"], 1)
        self.assertGreaterEqual(payload["counts"]["evaluation_benchmark_guidance_actions"], 3)
        self.assertEqual(
            payload["counts"]["frontier_theory_targets_scored"],
            payload["counts"]["frontier_theory_targets_total"],
        )
        self.assertEqual(
            payload["counts"]["frontier_theory_targets_total"],
            payload["counts"]["frontier_smoke_questions"],
        )
        self.assertGreater(payload["counts"]["frontier_theory_expected_results"], 0)
        self.assertGreaterEqual(payload["counts"]["fresh_holdout_frontier_entries"], 1)
        self.assertGreaterEqual(payload["counts"]["fresh_holdout_frontier_supported"], 1)
        self.assertGreaterEqual(payload["counts"]["fresh_holdout_frontier_scored_traces"], 1)
        self.assertGreater(payload["counts"]["fresh_holdout_frontier_expected_results"], 0)
        self.assertTrue(payload["counts"]["fresh_holdout_frontier_identity_withheld"])
        self.assertFalse(payload["counts"]["fresh_holdout_frontier_source_leakage_detected"])
        self.assertTrue(payload["counts"]["fresh_holdout_frontier_traces_ok"])
        self.assertTrue(payload["counts"]["fresh_holdout_frontier_all_ok"])
        self.assertEqual(payload["counts"]["research_intake_supported_accepted"], payload["counts"]["research_intake_supported"])
        self.assertEqual(payload["counts"]["research_intake_unsupported_rejected"], payload["counts"]["research_intake_unsupported"])
        self.assertEqual(payload["counts"]["adversarial_intake_ok"], payload["counts"]["adversarial_intake_cases"])
        self.assertEqual(payload["counts"]["adversarial_intake_rejected"], payload["counts"]["adversarial_intake_cases"])
        self.assertEqual(payload["counts"]["adversarial_intake_accepted"], 0)
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
        self.assertTrue(payload["counts"]["formal_source_graph_cache_enabled"])
        self.assertIn(payload["counts"]["formal_source_graph_cache_status"], {"hit", "miss"})
        self.assertTrue(payload["counts"]["formal_source_graph_cache_key"])
        self.assertEqual(
            payload["counts"]["formal_source_retrieval_benchmark_ok"],
            payload["counts"]["formal_source_retrieval_benchmark_cases"],
        )
        self.assertEqual(payload["counts"]["formal_source_retrieval_benchmark_recall_at_k"], 1.0)
        self.assertGreater(payload["counts"]["formal_source_retrieval_benchmark_mrr"], 0.0)
        self.assertEqual(
            payload["counts"]["formal_source_retrieval_ablation_lost_hits"],
            0,
        )
        self.assertGreaterEqual(payload["counts"]["formal_source_retrieval_ablation_cases"], 1)
        self.assertGreaterEqual(
            payload["counts"]["formal_source_retrieval_ablation_dependency_sensitive_cases"],
            0,
        )
        self.assertGreaterEqual(
            payload["counts"]["formal_source_retrieval_ablation_dependency_sensitive_new_hits"],
            0,
        )
        self.assertIn("lean_rag_dependency_graph_auto_discovered", payload["counts"])
        self.assertTrue(payload["counts"]["lean_rag_dependency_graph_enabled"])
        self.assertIn("timings", payload)
        self.assertGreater(payload["timings"]["total_elapsed_ms"], 0)
        self.assertTrue(payload["timings"]["stages"])
        self.assertTrue(payload["timings"]["slowest_stages"])
        timing_stages = {row["stage"] for row in payload["timings"]["stages"]}
        self.assertTrue({"research_benchmark", "research_benchmark_cache_hit"} & timing_stages)
        self.assertEqual(payload["counts"]["audit_total_elapsed_ms"], payload["timings"]["total_elapsed_ms"])
        self.assertTrue(payload["counts"]["audit_slowest_stage"])
        self.assertGreater(payload["counts"]["audit_slowest_stage_elapsed_ms"], 0)
        self.assertEqual(payload["counts"]["research_algorithms_ok"], payload["counts"]["research_algorithms_total"])
        self.assertGreater(payload["counts"]["algorithm_simulation_stress_cases"], 0)
        self.assertGreaterEqual(payload["counts"]["algorithm_simulation_stress_seeds"], 2)
        self.assertTrue(payload["counts"]["algorithm_simulation_stress_multi_seed_checked"])
        self.assertTrue(payload["counts"]["algorithm_simulation_stress_all_passed"])
        self.assertTrue(payload["counts"]["algorithm_simulation_stress_all_finite_metrics"])
        self.assertTrue(payload["counts"]["algorithm_simulation_stress_all_stress_ledgers_ok"])
        self.assertTrue(payload["counts"]["algorithm_simulation_stress_all_diagnoses_ok"])
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
        self.assertTrue(payload["counts"]["proof_search_policy_model_enabled"])
        self.assertGreater(payload["counts"]["proof_search_policy_scored_expanded_nodes"], 0)
        self.assertTrue(payload["counts"]["proof_search_value_model_enabled"])
        self.assertGreater(payload["counts"]["proof_search_value_scored_expanded_nodes"], 0)
        self.assertGreater(payload["counts"]["proof_search_tactic_template_candidates_total"], 0)
        self.assertGreater(payload["counts"]["proof_search_retrieval_candidates_total"], 0)
        self.assertTrue(payload["counts"]["proof_search_formal_source_retriever_enabled"])
        self.assertGreater(payload["counts"]["proof_search_formal_source_candidates_total"], 0)
        self.assertTrue(payload["counts"]["proof_search_retrieval_ablation_no_solved_regression"])
        self.assertGreaterEqual(payload["counts"]["proof_search_retrieval_ablation_candidate_delta"], 0)
        self.assertGreaterEqual(payload["counts"]["proof_search_retrieval_ablation_node_delta"], 0)
        proof_search_rag_ablation = json.loads(
            Path(payload["artifacts"]["proof_search_retrieval_ablation"]).read_text()
        )
        self.assertTrue(proof_search_rag_ablation["lean_rag_dependency_graph_enabled"])
        self.assertEqual(
            proof_search_rag_ablation["dependency_graph_search"],
            "lean_rag_dependency_graph",
        )
        self.assertGreater(payload["counts"]["proof_search_bootstrap_process_examples"], 0)
        self.assertGreater(payload["counts"]["prover_components_total"], 0)
        self.assertFalse(payload["counts"]["prover_component_goal_complete"])
        self.assertGreater(payload["counts"]["prover_components_ready"], 0)
        self.assertGreater(payload["counts"]["prover_components_partial"], 0)
        self.assertGreaterEqual(payload["counts"]["prover_components_missing_or_not_trained"], 0)
        self.assertEqual(payload["counts"]["research_traces_ok"], 10)
        self.assertGreater(payload["counts"]["theorem_goal_proof_obligations"], 0)
        self.assertEqual(
            payload["counts"]["verified_theorem_goal_proof_obligations"],
            payload["counts"]["theorem_goal_proof_obligations"],
        )
        self.assertGreater(payload["counts"]["unique_theorem_goal_proof_obligations"], 0)
        self.assertEqual(
            payload["counts"]["unique_verified_theorem_goal_proof_obligations"],
            payload["counts"]["unique_theorem_goal_proof_obligations"],
        )
        self.assertEqual(payload["counts"]["theorem_goal_proof_obligation_coverage_rate"], 1.0)
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
        self.assertEqual(payload["counts"]["autoform_targets_ok"], payload["counts"]["autoform_targets_total"])
        self.assertEqual(payload["counts"]["autoform_targets_total"], payload["counts"]["formal_gap_lean_tasks_total"])
        self.assertEqual(
            payload["counts"]["proof_bank_expansion_candidates_ok"],
            payload["counts"]["proof_bank_expansion_candidates_total"],
        )
        self.assertGreater(payload["counts"]["proof_bank_expansion_candidates_total"], 0)
        self.assertGreater(payload["counts"]["proof_bank_expansion_bridge_ready"], 0)
        self.assertGreater(payload["counts"]["proof_bank_expansion_blocked_placeholder"], 0)
        self.assertIn("proof_bank_expansion_compose_existing_bridge_chain", payload["counts"])
        self.assertIn("proof_bank_expansion_add_minimal_wrapper", payload["counts"])
        self.assertIn("proof_bank_expansion_design_bridge_lemma", payload["counts"])
        self.assertIn("proof_bank_expansion_design_from_first_principles", payload["counts"])
        self.assertEqual(
            payload["counts"]["proof_bank_expansion_candidates_total"],
            payload["counts"]["proof_bank_expansion_compose_existing_bridge_chain"]
            + payload["counts"]["proof_bank_expansion_add_minimal_wrapper"]
            + payload["counts"]["proof_bank_expansion_design_bridge_lemma"]
            + payload["counts"]["proof_bank_expansion_design_from_first_principles"],
        )
        self.assertEqual(
            payload["counts"]["primitive_source_coverage_primitives"],
            payload["counts"]["missing_formal_primitives"],
        )
        self.assertGreater(
            payload["counts"]["primitive_source_coverage_direct_wrapper_possible"]
            + payload["counts"]["primitive_source_coverage_bridge_lemma_needed"],
            0,
        )
        self.assertGreaterEqual(payload["counts"]["primitive_source_coverage_external_supported"], 0)
        self.assertIn("primitive_source_coverage_compose_existing_bridge_chain", payload["counts"])
        self.assertIn("primitive_source_coverage_add_minimal_wrapper", payload["counts"])
        self.assertIn("primitive_source_coverage_design_bridge_lemma", payload["counts"])
        self.assertIn("primitive_source_coverage_port_external_source", payload["counts"])
        self.assertIn("primitive_source_coverage_design_from_first_principles", payload["counts"])
        self.assertEqual(
            payload["counts"]["primitive_source_coverage_primitives"],
            payload["counts"]["primitive_source_coverage_compose_existing_bridge_chain"]
            + payload["counts"]["primitive_source_coverage_add_minimal_wrapper"]
            + payload["counts"]["primitive_source_coverage_design_bridge_lemma"]
            + payload["counts"]["primitive_source_coverage_port_external_source"]
            + payload["counts"]["primitive_source_coverage_design_from_first_principles"],
        )
        self.assertTrue(payload["counts"]["primitive_source_coverage_lean_rag_enabled"])
        self.assertEqual(payload["counts"]["research_training_traces"], payload["counts"]["questions"])
        self.assertGreaterEqual(payload["counts"]["research_training_sft_examples"], payload["counts"]["questions"] * 4)
        self.assertEqual(
            payload["counts"]["research_training_train"] + payload["counts"]["research_training_validation"],
            payload["counts"]["research_training_sft_examples"],
        )
        self.assertEqual(payload["counts"]["research_training_grpo_tasks"], payload["counts"]["questions"])
        self.assertEqual(payload["counts"]["research_policy_baseline_validation"], payload["counts"]["research_training_validation"])
        self.assertEqual(payload["counts"]["research_policy_baseline_valid_json"], payload["counts"]["research_policy_baseline_validation"])
        self.assertGreaterEqual(payload["counts"]["research_policy_baseline_same_task"], 0)
        self.assertGreaterEqual(payload["counts"]["research_policy_baseline_mean_json_key_f1"], 0.0)
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
        self.assertTrue(Path(payload["artifacts"]["adversarial_intake_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["adversarial_intake_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_knowledge_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_source_inventory"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_source_graph"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_source_graph_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_source_retrieval_benchmark"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_source_retrieval_benchmark_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_source_retrieval_ablation"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_source_retrieval_ablation_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["fresh_holdout_frontier_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["fresh_holdout_frontier_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_algorithm_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_simulation_stress_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_simulation_stress_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_attempt_log"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_training_export"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_training_train"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_training_validation"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_repair_export"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_repair_train"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_repair_validation"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_policy_baseline"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_policy_baseline_predictions"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_search_retrieval_ablation"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_search_retrieval_ablation_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["prover_component_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["prover_component_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_trace_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_gap_backlog"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formalization_target_audit"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formalization_target_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_gap_lean_tasks"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_gap_lean_tasks_jsonl"]).exists())
        self.assertTrue(Path(payload["artifacts"]["formal_gap_lean_tasks_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["autoform_targets"]).exists())
        self.assertTrue(Path(payload["artifacts"]["autoform_targets_yaml"]).exists())
        self.assertTrue(Path(payload["artifacts"]["autoform_targets_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_bank_expansion"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_bank_expansion_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_bank_expansion_lemma_proposals"]).exists())
        self.assertTrue(Path(payload["artifacts"]["proof_bank_expansion_theorem_hole_queue"]).exists())
        self.assertTrue(Path(payload["artifacts"]["primitive_source_coverage"]).exists())
        self.assertTrue(Path(payload["artifacts"]["primitive_source_coverage_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_training_export"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_training_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_training_train"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_training_validation"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_training_grpo"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_training_legacy_manifest"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_policy_baseline"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_policy_baseline_predictions"]).exists())
        self.assertTrue(Path(payload["artifacts"]["next_iteration_queue"]).exists())
        self.assertTrue(Path(payload["artifacts"]["next_iteration_queue_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_report"]).exists())
        self.assertTrue(Path(payload["artifacts"]["research_report_manifest"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_promotion"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_promotion_queue"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_sandbox"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_sandbox_results"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_sandbox_apply"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_sandbox_apply_results"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_sandbox_rerun"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_sandbox_rerun_results"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_sandbox_patch_eval"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_sandbox_patch_eval_results"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_patch_training_export"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_patch_training_train"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_patch_training_validation"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_patch_policy_model"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_patch_policy_model_json"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_patch_policy_validation_predictions"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_production_patch_plan"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_production_patch_plans"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_reviewed_patch_apply"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_reviewed_patch_apply_results"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_reviewed_patch_validate"]).exists())
        self.assertTrue(Path(payload["artifacts"]["algorithm_repair_reviewed_patch_validate_results"]).exists())
        self.assertTrue(Path(payload["artifacts"]["evaluation_benchmark_guidance"]).exists())
        self.assertTrue(Path(payload["artifacts"]["evaluation_benchmark_guidance_report"]).exists())


if __name__ == "__main__":
    unittest.main()
