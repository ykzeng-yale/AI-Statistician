"""Command-line interface for local orchestration utilities."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from statlean_agent.agents import AGENT_REGISTRY, get_agent
from statlean_agent.axle import (
    AXLE_BASE_URL,
    AXLE_DEFAULT_ENV,
    AxleClient,
    AxleError,
    read_source,
    render_payload_summary,
)
from statlean_agent.benchmarks import load_benchmarks, seed_benchmarks
from statlean_agent.blueprint import (
    blueprint_status,
    load_blueprint,
    render_blueprint_status,
    validate_blueprint,
)
from statlean_agent.contracts import LemmaProposal, ProofAttempt, VerificationReport
from statlean_agent.curation import (
    build_lemma_proposal_gate_reports,
    build_lemma_non_vacuity_reports,
    build_lemma_proof_cost_reports,
    build_theorem_hole_lemma_ledger,
    build_theorem_hole_lemma_proposals,
    build_theorem_hole_promotion_queue,
)
from statlean_agent.evaluation import (
    DEFAULT_REPRODUCIBILITY_ARTIFACTS,
    build_ablation_report,
    build_concrete_estimator_chain_report,
    build_empirical_process_expansion_targets,
    build_empirical_process_external_prover_slice,
    build_external_baseline_plan,
    build_external_baseline_results,
    build_paper_quality_heldout_report,
    build_reproducibility_bundle,
    build_vdvw_bracketing_gc_statement_candidates,
    build_vdvw_theorem_inventory,
    compare_baseline_on_split,
    evaluate_attempts,
    summarize_benchmark_attempts,
)
from statlean_agent.orchestrator import DEFAULT_WORKFLOW
from statlean_agent.retrieval import PremiseRecord, build_premise_index, search_premises
from statlean_agent.serialization import dataclass_from_dict, dumps_json, read_jsonl, write_jsonl
from statlean_agent.training import build_grpo_process_tasks, build_rejected_dpo_attempts, build_training_manifest
from statlean_agent.verifier import LakeVerifier, render_task
from statlean_agent.worktrees import WorktreeManager


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="statlean")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-agents", help="List configured agents.")
    subparsers.add_parser("workflow", help="Print the default workflow.")

    blueprint = subparsers.add_parser("blueprint-status", help="Print current phase blueprint status.")
    blueprint.add_argument("--blueprint", default="config/statlean_blueprint.json", help="Blueprint JSON path.")
    blueprint.add_argument("--json", action="store_true", help="Emit machine-readable status JSON.")

    seed = subparsers.add_parser("seed-benchmarks", help="Write seed benchmark tasks.")
    seed.add_argument("--output", default="benchmarks/seeds.jsonl", help="Output JSONL path.")

    list_benchmarks = subparsers.add_parser("list-benchmarks", help="List benchmark tasks.")
    list_benchmarks.add_argument("--input", default="benchmarks/seeds.jsonl", help="Input JSONL path.")

    render = subparsers.add_parser("render-task", help="Render one benchmark task as Lean source.")
    render.add_argument("task_id", help="Benchmark task id.")
    render.add_argument("--input", default="benchmarks/seeds.jsonl", help="Input JSONL path.")

    verify = subparsers.add_parser("verify-task", help="Verify one benchmark task using local Lake.")
    verify.add_argument("task_id", help="Benchmark task id.")
    verify.add_argument("--input", default="benchmarks/seeds.jsonl", help="Input JSONL path.")
    verify.add_argument("--repo", default=".", help="Lake repository root.")
    verify.add_argument("--timeout", type=int, default=60, help="Verification timeout in seconds.")

    verify_all = subparsers.add_parser("verify-benchmarks", help="Verify all benchmark tasks using local Lake.")
    verify_all.add_argument("--input", default="benchmarks/seeds.jsonl", help="Input JSONL path.")
    verify_all.add_argument("--output", default="artifacts/verification/reports.jsonl", help="Output JSONL path.")
    verify_all.add_argument("--repo", default=".", help="Lake repository root.")
    verify_all.add_argument("--timeout", type=int, default=60, help="Verification timeout in seconds.")
    verify_all.add_argument("--allow-failures", action="store_true", help="Return success even when tasks fail.")

    axle_tool = subparsers.add_parser("axle-tool", help="Run one AXLE Lean Engine tool on a Lean source file.")
    axle_tool.add_argument(
        "tool",
        choices=(
            "check",
            "extract_decls",
            "extract_theorems",
            "theorem2sorry",
            "theorem2lemma",
            "have2sorry",
            "have2lemma",
            "sorry2lemma",
            "normalize",
            "simplify_theorems",
            "repair_proofs",
            "disprove",
        ),
        help="AXLE tool name.",
    )
    axle_tool.add_argument("input", help="Lean source file.")
    axle_tool.add_argument("--output", help="Optional JSON response output path.")
    axle_tool.add_argument("--content-output", help="Optional path for response['content'].")
    axle_tool.add_argument("--env", default=AXLE_DEFAULT_ENV, help="AXLE Lean environment.")
    axle_tool.add_argument("--base-url", default=AXLE_BASE_URL, help="AXLE base URL.")
    axle_tool.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds.")
    axle_tool.add_argument(
        "--ignore-imports",
        action="store_true",
        help="Ask AXLE to tolerate imports that differ from the selected environment.",
    )
    axle_tool.add_argument("--json", action="store_true", help="Print full JSON response.")

    axle_verify = subparsers.add_parser(
        "axle-verify-proof",
        help="Use AXLE verify_proof to validate one candidate against a statement file.",
    )
    axle_verify.add_argument("--statement", required=True, help="Lean file containing the expected formal statement.")
    axle_verify.add_argument("--content", required=True, help="Lean file containing the candidate proof.")
    axle_verify.add_argument("--output", help="Optional JSON response output path.")
    axle_verify.add_argument("--env", default=AXLE_DEFAULT_ENV, help="AXLE Lean environment.")
    axle_verify.add_argument("--base-url", default=AXLE_BASE_URL, help="AXLE base URL.")
    axle_verify.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds.")
    axle_verify.add_argument(
        "--ignore-imports",
        action="store_true",
        help="Ask AXLE to tolerate imports that differ from the selected environment.",
    )
    axle_verify.add_argument("--json", action="store_true", help="Print full JSON response.")

    materialize_attempts = subparsers.add_parser(
        "materialize-benchmark-attempts",
        help="Render benchmark tasks into ProofAttempt JSONL records for evaluation.",
    )
    materialize_attempts.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    materialize_attempts.add_argument(
        "--output",
        default="artifacts/evaluation/benchmark-seed-attempts.jsonl",
        help="Output ProofAttempt JSONL path.",
    )
    materialize_attempts.add_argument(
        "--agent-key",
        default="seed-registry",
        help="Agent key to attach to rendered benchmark attempts.",
    )

    eval_attempts = subparsers.add_parser("eval-attempts", help="Evaluate proof attempts and reports.")
    eval_attempts.add_argument("--attempts", required=True, help="ProofAttempt JSONL path.")
    eval_attempts.add_argument("--reports", required=True, help="VerificationReport JSONL path.")

    verify_attempts = subparsers.add_parser("verify-attempts", help="Verify ProofAttempt JSONL records using local Lake.")
    verify_attempts.add_argument("--attempts", required=True, help="ProofAttempt JSONL path.")
    verify_attempts.add_argument("--output", required=True, help="Output VerificationReport JSONL path.")
    verify_attempts.add_argument("--repo", default=".", help="Lake repository root.")
    verify_attempts.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    verify_attempts.add_argument("--timeout", type=int, default=60, help="Verification timeout in seconds.")
    verify_attempts.add_argument("--allow-failures", action="store_true", help="Return success even when attempts fail.")

    eval_summary = subparsers.add_parser("eval-summary", help="Summarize benchmark attempts by metadata.")
    eval_summary.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    eval_summary.add_argument("--attempts", required=True, help="ProofAttempt JSONL path.")
    eval_summary.add_argument("--reports", required=True, help="VerificationReport JSONL path.")
    eval_summary.add_argument("--output", help="Optional summary JSON output path.")

    baseline_compare = subparsers.add_parser(
        "baseline-comparison",
        help="Compare one baseline on a held-out benchmark split.",
    )
    baseline_compare.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    baseline_compare.add_argument("--attempts", required=True, help="ProofAttempt JSONL path.")
    baseline_compare.add_argument("--reports", required=True, help="VerificationReport JSONL path.")
    baseline_compare.add_argument("--baseline", default="seed-registry", help="ProofAttempt agent_key to evaluate.")
    baseline_compare.add_argument("--split", default="test", help="Benchmark split to evaluate.")
    baseline_compare.add_argument("--output", help="Optional comparison JSON output path.")

    external_baselines = subparsers.add_parser(
        "external-baseline-plan",
        help="Build a post-P8 external prover baseline run plan.",
    )
    external_baselines.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    external_baselines.add_argument("--split", default="test", help="Benchmark split targeted by external baselines.")
    external_baselines.add_argument(
        "--output-dir",
        default="artifacts/external_baselines",
        help="Output directory encoded for future external baseline attempts/reports.",
    )
    external_baselines.add_argument(
        "--output",
        default="artifacts/evaluation/external-baseline-plan.json",
        help="Output external baseline plan JSON path.",
    )

    external_results = subparsers.add_parser(
        "external-baseline-results",
        help="Ingest and compare available external baseline attempt/report files.",
    )
    external_results.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    external_results.add_argument(
        "--plan",
        default="artifacts/evaluation/external-baseline-plan.json",
        help="External baseline plan JSON path.",
    )
    external_results.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve plan result paths.",
    )
    external_results.add_argument(
        "--seed-attempts",
        default="artifacts/evaluation/benchmark-seed-attempts.jsonl",
        help="Fallback seed-registry ProofAttempt JSONL path.",
    )
    external_results.add_argument(
        "--seed-reports",
        default="artifacts/verification/benchmark-seed-reports.jsonl",
        help="Fallback seed-registry VerificationReport JSONL path.",
    )
    external_results.add_argument(
        "--output",
        default="artifacts/evaluation/external-baseline-results.json",
        help="Output external baseline results JSON path.",
    )

    empirical_process_targets = subparsers.add_parser(
        "empirical-process-targets",
        help="Build the P9 empirical-process expansion target map.",
    )
    empirical_process_targets.add_argument(
        "--benchmarks",
        default="benchmarks/seeds.jsonl",
        help="BenchmarkTask JSONL path.",
    )
    empirical_process_targets.add_argument(
        "--output",
        default="artifacts/evaluation/empirical-process-targets.json",
        help="Output empirical-process target JSON path.",
    )

    empirical_process_external_slice = subparsers.add_parser(
        "empirical-process-external-slice",
        help="Build the P10 empirical-process external prover evaluation slice.",
    )
    empirical_process_external_slice.add_argument(
        "--benchmarks",
        default="benchmarks/seeds.jsonl",
        help="BenchmarkTask JSONL path.",
    )
    empirical_process_external_slice.add_argument(
        "--targets",
        default="artifacts/evaluation/empirical-process-targets.json",
        help="Empirical-process targets JSON path.",
    )
    empirical_process_external_slice.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve planned external result paths.",
    )
    empirical_process_external_slice.add_argument(
        "--output-dir",
        default="artifacts/external_baselines/empirical_process",
        help="Output directory encoded for future empirical-process external baseline files.",
    )
    empirical_process_external_slice.add_argument(
        "--seed-attempts",
        default="artifacts/evaluation/benchmark-seed-attempts.jsonl",
        help="Fallback seed-registry ProofAttempt JSONL path.",
    )
    empirical_process_external_slice.add_argument(
        "--seed-reports",
        default="artifacts/verification/benchmark-seed-reports.jsonl",
        help="Fallback seed-registry VerificationReport JSONL path.",
    )
    empirical_process_external_slice.add_argument(
        "--output",
        default="artifacts/evaluation/empirical-process-external-slice.json",
        help="Output empirical-process external slice JSON path.",
    )

    vdvw_inventory = subparsers.add_parser(
        "vdvw-theorem-inventory",
        help="Build the P11 source-linked VdV&W theorem inventory and semantic audit.",
    )
    vdvw_inventory.add_argument(
        "--benchmarks",
        default="benchmarks/seeds.jsonl",
        help="BenchmarkTask JSONL path.",
    )
    vdvw_inventory.add_argument(
        "--output",
        default="artifacts/research/vdvw-theorem-inventory.json",
        help="Output VdV&W theorem inventory JSON path.",
    )

    vdvw_bracketing_gc = subparsers.add_parser(
        "vdvw-bracketing-gc-statements",
        help="Build P11.M2 VdV&W Theorem 2.4.1 bracketing GC statement candidates.",
    )
    vdvw_bracketing_gc.add_argument(
        "--benchmarks",
        default="benchmarks/seeds.jsonl",
        help="BenchmarkTask JSONL path.",
    )
    vdvw_bracketing_gc.add_argument(
        "--output",
        default="artifacts/research/vdvw-bracketing-gc-statement-candidates.json",
        help="Output bracketing GC statement-candidates JSON path.",
    )

    paper_heldout = subparsers.add_parser(
        "paper-quality-heldout",
        help="Build a paper-quality held-out report with proof-chain coverage.",
    )
    paper_heldout.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    paper_heldout.add_argument("--attempts", required=True, help="ProofAttempt JSONL path.")
    paper_heldout.add_argument("--reports", required=True, help="VerificationReport JSONL path.")
    paper_heldout.add_argument("--baseline", default="seed-registry", help="ProofAttempt agent_key to evaluate.")
    paper_heldout.add_argument("--split", default="test", help="Benchmark split to evaluate.")
    paper_heldout.add_argument(
        "--output",
        default="artifacts/evaluation/paper-quality-heldout.json",
        help="Output paper-quality held-out JSON path.",
    )

    concrete_chain = subparsers.add_parser(
        "concrete-estimator-chain-report",
        help="Build the P8 concrete estimator proof-chain report.",
    )
    concrete_chain.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    concrete_chain.add_argument(
        "--reports",
        default="artifacts/verification/benchmark-seed-reports.jsonl",
        help="VerificationReport JSONL path.",
    )
    concrete_chain.add_argument(
        "--task-id",
        default="paper_quality_ipw_hajek_concrete_chain_seed",
        help="Concrete estimator chain benchmark task id.",
    )
    concrete_chain.add_argument(
        "--output",
        default="artifacts/evaluation/concrete-estimator-chain.json",
        help="Output concrete estimator chain JSON path.",
    )

    ablation_report = subparsers.add_parser(
        "ablation-report",
        help="Build the P8 artifact-backed component ablation report.",
    )
    ablation_report.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    ablation_report.add_argument(
        "--paper-heldout",
        default="artifacts/evaluation/paper-quality-heldout.json",
        help="Paper-quality held-out JSON path.",
    )
    ablation_report.add_argument(
        "--concrete-chain",
        default="artifacts/evaluation/concrete-estimator-chain.json",
        help="Concrete estimator chain JSON path.",
    )
    ablation_report.add_argument(
        "--training-manifest",
        default="artifacts/training/manifest.json",
        help="Training manifest JSON path.",
    )
    ablation_report.add_argument(
        "--grpo-tasks",
        default="artifacts/training/grpo-process-tasks.jsonl",
        help="GRPO process-task JSONL path.",
    )
    ablation_report.add_argument(
        "--dpo-reports",
        default="artifacts/training/dpo-negative-reports.jsonl",
        help="DPO rejected VerificationReport JSONL path.",
    )
    ablation_report.add_argument(
        "--lemma-proposal-gates",
        default="artifacts/curation/lemma-proposal-gates.jsonl",
        help="Lemma proposal gate JSONL path.",
    )
    ablation_report.add_argument(
        "--lemma-non-vacuity",
        default="artifacts/curation/lemma-non-vacuity.jsonl",
        help="Lemma non-vacuity report JSONL path.",
    )
    ablation_report.add_argument(
        "--lemma-proof-cost",
        default="artifacts/curation/lemma-proof-cost.jsonl",
        help="Lemma proof-cost report JSONL path.",
    )
    ablation_report.add_argument(
        "--lemma-ledger",
        default="artifacts/curation/theorem-hole-ledger.jsonl",
        help="Curated theorem-hole lemma ledger JSONL path.",
    )
    ablation_report.add_argument(
        "--output",
        default="artifacts/evaluation/ablation-report.json",
        help="Output ablation report JSON path.",
    )

    reproducibility_bundle = subparsers.add_parser(
        "reproducibility-bundle",
        help="Build the P8 research reproducibility bundle with artifact hashes.",
    )
    reproducibility_bundle.add_argument("--repo-root", default=".", help="Repository root.")
    reproducibility_bundle.add_argument("--blueprint", default="config/statlean_blueprint.json", help="Blueprint JSON path.")
    reproducibility_bundle.add_argument(
        "--paper-draft",
        default="docs/paper_draft.md",
        help="Paper draft path included in the bundle.",
    )
    reproducibility_bundle.add_argument(
        "--artifact",
        action="append",
        dest="artifacts",
        help="Artifact path to hash. May be repeated. Defaults to the P8 bundle set.",
    )
    reproducibility_bundle.add_argument(
        "--output",
        default="artifacts/evaluation/reproducibility-bundle.json",
        help="Output reproducibility bundle JSON path.",
    )

    lemma_ledger = subparsers.add_parser(
        "build-lemma-ledger",
        help="Build a curator-gated lemma-growth ledger from theorem-hole benchmark tasks.",
    )
    lemma_ledger.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    lemma_ledger.add_argument(
        "--reports",
        default="artifacts/verification/benchmark-seed-reports.jsonl",
        help="VerificationReport JSONL path.",
    )
    lemma_ledger.add_argument(
        "--output",
        default="artifacts/curation/theorem-hole-ledger.jsonl",
        help="Output CuratedLemmaLedgerEntry JSONL path.",
    )

    lemma_proposals = subparsers.add_parser(
        "build-lemma-proposals",
        help="Build pre-curation lemma proposal records from theorem-hole benchmark tasks.",
    )
    lemma_proposals.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    lemma_proposals.add_argument(
        "--output",
        default="artifacts/curation/lemma-proposals.jsonl",
        help="Output LemmaProposal JSONL path.",
    )
    lemma_proposals.add_argument(
        "--proposed-by",
        default="theorem-hole-miner",
        help="Proposal source identifier.",
    )

    theorem_hole_queue = subparsers.add_parser(
        "theorem-hole-promotion-queue",
        help="Build the P9 theorem-hole no-placeholder promotion queue.",
    )
    theorem_hole_queue.add_argument(
        "--benchmarks",
        default="benchmarks/seeds.jsonl",
        help="BenchmarkTask JSONL path.",
    )
    theorem_hole_queue.add_argument(
        "--output",
        default="artifacts/curation/theorem-hole-promotion-queue.json",
        help="Output theorem-hole promotion queue JSON path.",
    )

    lemma_proposal_gates = subparsers.add_parser(
        "check-lemma-proposals",
        help="Run duplicate and import-minimality checks for lemma proposals.",
    )
    lemma_proposal_gates.add_argument(
        "--proposals",
        default="artifacts/curation/lemma-proposals.jsonl",
        help="LemmaProposal JSONL path.",
    )
    lemma_proposal_gates.add_argument(
        "--output",
        default="artifacts/curation/lemma-proposal-gates.jsonl",
        help="Output LemmaProposalGateReport JSONL path.",
    )
    lemma_proposal_gates.add_argument("--root", default=".", help="Repository root for premise indexing.")
    lemma_proposal_gates.add_argument("--source-dir", default="StatInference", help="Lean source directory.")
    lemma_proposal_gates.add_argument(
        "--premises",
        help="Optional existing PremiseRecord JSONL path. If omitted, index local Lean declarations.",
    )

    lemma_non_vacuity = subparsers.add_parser(
        "check-lemma-non-vacuity",
        help="Require accepted non-vacuity benchmark evidence for lemma proposals.",
    )
    lemma_non_vacuity.add_argument(
        "--proposals",
        default="artifacts/curation/lemma-proposals.jsonl",
        help="LemmaProposal JSONL path.",
    )
    lemma_non_vacuity.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    lemma_non_vacuity.add_argument(
        "--reports",
        default="artifacts/verification/benchmark-seed-reports.jsonl",
        help="VerificationReport JSONL path.",
    )
    lemma_non_vacuity.add_argument(
        "--output",
        default="artifacts/curation/lemma-non-vacuity.jsonl",
        help="Output LemmaNonVacuityReport JSONL path.",
    )

    lemma_proof_cost = subparsers.add_parser(
        "check-lemma-proof-cost",
        help="Estimate downstream proof-cost improvement for lemma proposals.",
    )
    lemma_proof_cost.add_argument(
        "--proposals",
        default="artifacts/curation/lemma-proposals.jsonl",
        help="LemmaProposal JSONL path.",
    )
    lemma_proof_cost.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    lemma_proof_cost.add_argument(
        "--output",
        default="artifacts/curation/lemma-proof-cost.jsonl",
        help="Output LemmaProofCostReport JSONL path.",
    )

    index_premises = subparsers.add_parser("index-premises", help="Index local Lean declarations.")
    index_premises.add_argument("--root", default=".", help="Repository root.")
    index_premises.add_argument("--source-dir", default="StatInference", help="Lean source directory.")
    index_premises.add_argument("--output", default="artifacts/premise_index/local.jsonl", help="Output JSONL path.")

    search = subparsers.add_parser("search-premises", help="Search a premise index.")
    search.add_argument("query", help="Search query.")
    search.add_argument("--index", default="artifacts/premise_index/local.jsonl", help="Premise index JSONL.")
    search.add_argument("--top-k", type=int, default=8, help="Number of matches.")

    train_manifest = subparsers.add_parser("build-training-manifest", help="Build SFT/DPO/GRPO manifest.")
    train_manifest.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="Benchmark JSONL path.")
    train_manifest.add_argument("--output", default="artifacts/training/manifest.json", help="Manifest JSON path.")
    train_manifest.add_argument("--run-id", default="local-seed", help="Run id.")
    train_manifest.add_argument("--base-model", default="unspecified-lean-prover", help="Base model name.")
    train_manifest.add_argument("--attempts", help="Optional verified ProofAttempt JSONL path.")
    train_manifest.add_argument("--reports", help="Optional VerificationReport JSONL path paired with attempts.")
    train_manifest.add_argument("--rejected-attempts", help="Optional rejected ProofAttempt JSONL path for DPO.")
    train_manifest.add_argument("--rejected-reports", help="Optional rejected VerificationReport JSONL path for DPO.")

    dpo_rejections = subparsers.add_parser(
        "materialize-dpo-rejections",
        help="Create deterministic rejected attempts for DPO from benchmark theorem statements.",
    )
    dpo_rejections.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    dpo_rejections.add_argument(
        "--output",
        default="artifacts/training/dpo-negative-attempts.jsonl",
        help="Output rejected ProofAttempt JSONL path.",
    )
    dpo_rejections.add_argument(
        "--agent-key",
        default="dpo-negative-generator",
        help="Agent key to attach to generated rejected attempts.",
    )

    grpo_tasks = subparsers.add_parser(
        "materialize-grpo-tasks",
        help="Create process-reward GRPO task JSONL with verifier and policy metadata.",
    )
    grpo_tasks.add_argument("--benchmarks", default="benchmarks/seeds.jsonl", help="BenchmarkTask JSONL path.")
    grpo_tasks.add_argument(
        "--output",
        default="artifacts/training/grpo-process-tasks.jsonl",
        help="Output GRPO process task JSONL path.",
    )
    grpo_tasks.add_argument("--repo", default=".", help="Lake repository root for verifier commands.")
    grpo_tasks.add_argument("--timeout", type=int, default=120, help="Verifier timeout encoded in each task.")
    grpo_tasks.add_argument(
        "--python",
        default="python",
        help="Python executable encoded in each verifier command.",
    )

    assign = subparsers.add_parser("assign-worktree", help="Create or preview an agent worktree.")
    assign.add_argument("--agent", required=True, help="Agent key.")
    assign.add_argument("--base", default="main", help="Base branch.")
    assign.add_argument("--repo", default=".", help="Repository root.")
    assign.add_argument("--dry-run", action="store_true", help="Preview without creating worktree.")

    args = parser.parse_args(argv)
    if args.command == "list-agents":
        for agent in AGENT_REGISTRY:
            print(f"{agent.key}: {agent.name}")
        return 0

    if args.command == "workflow":
        for index, stage in enumerate(DEFAULT_WORKFLOW, start=1):
            print(f"{index}. {stage.name}: {', '.join(stage.agents)} -> {stage.output}")
        return 0

    if args.command == "blueprint-status":
        blueprint_data = load_blueprint(Path(args.blueprint))
        errors = validate_blueprint(blueprint_data)
        if errors:
            for error in errors:
                print(f"error: {error}")
            return 1
        if args.json:
            print(dumps_json(blueprint_status(blueprint_data)))
        else:
            print(render_blueprint_status(blueprint_data))
        return 0

    if args.command == "seed-benchmarks":
        path = Path(args.output)
        seed_benchmarks(path)
        print(f"wrote {path}")
        return 0

    if args.command == "list-benchmarks":
        tasks = load_benchmarks(Path(args.input))
        for task in tasks:
            print(f"{task.task_id}\t{task.task_type.value}\t{task.split.value}\t{','.join(task.domain_tags)}")
        return 0

    if args.command == "render-task":
        task = _find_task(Path(args.input), args.task_id)
        print(render_task(task.lean_task))
        return 0

    if args.command == "verify-task":
        task = _find_task(Path(args.input), args.task_id)
        verifier = LakeVerifier(Path(args.repo), timeout_seconds=args.timeout)
        report = verifier.verify_task(task.lean_task)
        print(f"status={report.status.value}")
        if report.first_error:
            print(f"first_error={report.first_error}")
        for diagnostic in report.diagnostics:
            print(diagnostic)
        return 0 if report.status.value == "accepted" else 1

    if args.command == "verify-benchmarks":
        tasks = load_benchmarks(Path(args.input))
        verifier = LakeVerifier(Path(args.repo), timeout_seconds=args.timeout)
        reports = [verifier.verify_task(task.lean_task) for task in tasks]
        write_jsonl(Path(args.output), reports)
        accepted = sum(1 for report in reports if report.status.value == "accepted")
        print(f"verified={len(reports)} accepted={accepted} output={args.output}")
        if accepted == len(reports) or args.allow_failures:
            return 0
        return 1

    if args.command == "axle-tool":
        client = AxleClient.from_env(base_url=args.base_url, timeout_seconds=args.timeout)
        try:
            payload = client.transform_code(
                args.tool,
                read_source(Path(args.input)),
                env=args.env,
                ignore_imports=args.ignore_imports or None,
                timeout_seconds=args.timeout,
            )
        except AxleError as error:
            print(str(error))
            return 1
        _write_optional_json(Path(args.output) if args.output else None, payload)
        if args.content_output:
            content = payload.get("content")
            if not isinstance(content, str):
                raise SystemExit("AXLE response has no string `content` field")
            content_output = Path(args.content_output)
            content_output.parent.mkdir(parents=True, exist_ok=True)
            content_output.write_text(content, encoding="utf-8")
        if args.json:
            print(dumps_json(payload))
        else:
            print(render_payload_summary(payload))
        return 0

    if args.command == "axle-verify-proof":
        client = AxleClient.from_env(base_url=args.base_url, timeout_seconds=args.timeout)
        try:
            payload = client.verify_proof(
                formal_statement=read_source(Path(args.statement)),
                content=read_source(Path(args.content)),
                env=args.env,
                ignore_imports=args.ignore_imports or None,
                timeout_seconds=args.timeout,
            )
        except AxleError as error:
            print(str(error))
            return 1
        _write_optional_json(Path(args.output) if args.output else None, payload)
        if args.json:
            print(dumps_json(payload))
        else:
            print(render_payload_summary(payload))
        return 0

    if args.command == "materialize-benchmark-attempts":
        tasks = load_benchmarks(Path(args.benchmarks))
        attempts = [
            ProofAttempt(
                task_id=task.task_id,
                agent_key=args.agent_key,
                lean_code=render_task(task.lean_task),
                premises_used=task.expected_premises,
            )
            for task in tasks
        ]
        write_jsonl(Path(args.output), attempts)
        print(f"materialized={len(attempts)} output={args.output}")
        return 0

    if args.command == "eval-attempts":
        attempts = tuple(dataclass_from_dict(ProofAttempt, record) for record in read_jsonl(Path(args.attempts)))
        reports = tuple(
            dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
        )
        print(dumps_json(evaluate_attempts(attempts, reports)))
        return 0

    if args.command == "verify-attempts":
        attempts = tuple(dataclass_from_dict(ProofAttempt, record) for record in read_jsonl(Path(args.attempts)))
        tasks = load_benchmarks(Path(args.benchmarks))
        allowed_by_task = {task.task_id: ("sorry",) if task.lean_task.allowed_sorry else () for task in tasks}
        verifier = LakeVerifier(Path(args.repo), timeout_seconds=args.timeout)
        reports = [
            verifier.verify_source(
                attempt.task_id,
                attempt.lean_code,
                allowed_placeholders=allowed_by_task.get(attempt.task_id, ()),
            )
            for attempt in attempts
        ]
        write_jsonl(Path(args.output), reports)
        accepted = sum(1 for report in reports if report.status.value == "accepted")
        print(f"verified={len(reports)} accepted={accepted} output={args.output}")
        if accepted == len(reports) or args.allow_failures:
            return 0
        return 1

    if args.command == "eval-summary":
        tasks = load_benchmarks(Path(args.benchmarks))
        attempts = tuple(dataclass_from_dict(ProofAttempt, record) for record in read_jsonl(Path(args.attempts)))
        reports = tuple(
            dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
        )
        summary = summarize_benchmark_attempts(tasks, attempts, reports)
        encoded = dumps_json(summary)
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(encoded + "\n", encoding="utf-8")
            print(f"wrote {output}")
        else:
            print(encoded)
        return 0

    if args.command == "baseline-comparison":
        tasks = load_benchmarks(Path(args.benchmarks))
        attempts = tuple(dataclass_from_dict(ProofAttempt, record) for record in read_jsonl(Path(args.attempts)))
        reports = tuple(
            dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
        )
        comparison = compare_baseline_on_split(
            tasks,
            attempts,
            reports,
            baseline=args.baseline,
            split=args.split,
        )
        encoded = dumps_json(comparison)
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(encoded + "\n", encoding="utf-8")
            print(f"wrote {output}")
        else:
            print(encoded)
        return 0

    if args.command == "external-baseline-plan":
        tasks = load_benchmarks(Path(args.benchmarks))
        plan = build_external_baseline_plan(
            tasks,
            split=args.split,
            benchmark_path=args.benchmarks,
            output_dir=args.output_dir,
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(plan) + "\n", encoding="utf-8")
        print(
            f"wrote {output} baselines={plan['baseline_count']} "
            f"ready={plan['ready_baseline_count']} target_tasks={plan['target_task_count']}"
        )
        return 0

    if args.command == "external-baseline-results":
        tasks = load_benchmarks(Path(args.benchmarks))
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        root = Path(args.repo_root)
        attempts_by_baseline: dict[str, tuple[ProofAttempt, ...]] = {}
        reports_by_baseline: dict[str, tuple[VerificationReport, ...]] = {}
        source_by_baseline: dict[str, str] = {}

        for baseline in plan.get("baselines", ()):
            if not isinstance(baseline, dict):
                continue
            baseline_id = str(baseline.get("baseline_id", ""))
            attempts_path = root / str(baseline.get("attempts_path", ""))
            reports_path = root / str(baseline.get("reports_path", ""))
            if attempts_path.exists() and reports_path.exists():
                attempts_by_baseline[baseline_id] = tuple(
                    dataclass_from_dict(ProofAttempt, record)
                    for record in read_jsonl(attempts_path)
                )
                reports_by_baseline[baseline_id] = tuple(
                    dataclass_from_dict(VerificationReport, record)
                    for record in read_jsonl(reports_path)
                )
                source_by_baseline[baseline_id] = "planned_result_files"
                continue

            if baseline_id == "seed-registry":
                attempts_by_baseline[baseline_id] = tuple(
                    dataclass_from_dict(ProofAttempt, record)
                    for record in read_jsonl(Path(args.seed_attempts))
                )
                reports_by_baseline[baseline_id] = tuple(
                    dataclass_from_dict(VerificationReport, record)
                    for record in read_jsonl(Path(args.seed_reports))
                )
                source_by_baseline[baseline_id] = "checked_in_seed_registry_fallback"

        report = build_external_baseline_results(
            tasks,
            plan,
            attempts_by_baseline,
            reports_by_baseline,
            source_by_baseline=source_by_baseline,
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"external_results={report['baseline_count']} ingested={report['ingested_count']} "
            f"blocked={report['blocked_count']} best={report['best_available_baseline']} "
            f"output={args.output}"
        )
        return 0

    if args.command == "empirical-process-targets":
        tasks = load_benchmarks(Path(args.benchmarks))
        report = build_empirical_process_expansion_targets(tasks)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"empirical_process_targets={report['target_count']} "
            f"scoped={report['scoped_count']} pending={report['pending_count']} "
            f"output={args.output}"
        )
        return 0

    if args.command == "empirical-process-external-slice":
        tasks = load_benchmarks(Path(args.benchmarks))
        target_report = json.loads(Path(args.targets).read_text(encoding="utf-8"))
        root = Path(args.repo_root)
        attempts_by_baseline: dict[str, tuple[ProofAttempt, ...]] = {}
        reports_by_baseline: dict[str, tuple[VerificationReport, ...]] = {}
        source_by_baseline: dict[str, str] = {}

        provisional = build_empirical_process_external_prover_slice(
            tasks,
            target_report,
            {},
            {},
            benchmark_path=args.benchmarks,
            output_dir=args.output_dir,
        )
        for baseline in provisional.get("rows", ()):
            if not isinstance(baseline, dict):
                continue
            baseline_id = str(baseline.get("baseline_id", ""))
            attempts_path = root / str(baseline.get("attempts_path", ""))
            reports_path = root / str(baseline.get("reports_path", ""))
            if attempts_path.exists() and reports_path.exists():
                attempts_by_baseline[baseline_id] = tuple(
                    dataclass_from_dict(ProofAttempt, record)
                    for record in read_jsonl(attempts_path)
                )
                reports_by_baseline[baseline_id] = tuple(
                    dataclass_from_dict(VerificationReport, record)
                    for record in read_jsonl(reports_path)
                )
                source_by_baseline[baseline_id] = "planned_empirical_process_result_files"
                continue

            if baseline_id == "seed-registry":
                attempts_by_baseline[baseline_id] = tuple(
                    dataclass_from_dict(ProofAttempt, record)
                    for record in read_jsonl(Path(args.seed_attempts))
                )
                reports_by_baseline[baseline_id] = tuple(
                    dataclass_from_dict(VerificationReport, record)
                    for record in read_jsonl(Path(args.seed_reports))
                )
                source_by_baseline[baseline_id] = "checked_in_seed_registry_fallback"

        report = build_empirical_process_external_prover_slice(
            tasks,
            target_report,
            attempts_by_baseline,
            reports_by_baseline,
            source_by_baseline=source_by_baseline,
            benchmark_path=args.benchmarks,
            output_dir=args.output_dir,
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"empirical_process_external_slice={report['target_task_count']} "
            f"families={report['family_count']} ingested={report['ingested_count']} "
            f"blocked={report['blocked_count']} best={report['best_available_baseline']} "
            f"output={args.output}"
        )
        return 0

    if args.command == "vdvw-theorem-inventory":
        tasks = load_benchmarks(Path(args.benchmarks))
        report = build_vdvw_theorem_inventory(tasks)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"vdvw_theorem_inventory={report['row_count']} "
            f"families={len(report['family_counts'])} "
            f"blocked_or_review={len(report['blocked_or_review_rows'])} "
            f"output={args.output}"
        )
        return 0

    if args.command == "vdvw-bracketing-gc-statements":
        tasks = load_benchmarks(Path(args.benchmarks))
        report = build_vdvw_bracketing_gc_statement_candidates(tasks)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"vdvw_bracketing_gc_statement_candidates={report['candidate_count']} "
            f"tracks={len(report['track_counts'])} "
            f"blocked_or_review={len(report['blocked_or_review_candidates'])} "
            f"output={args.output}"
        )
        return 0

    if args.command == "paper-quality-heldout":
        tasks = load_benchmarks(Path(args.benchmarks))
        attempts = tuple(dataclass_from_dict(ProofAttempt, record) for record in read_jsonl(Path(args.attempts)))
        reports = tuple(
            dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
        )
        report = build_paper_quality_heldout_report(
            tasks,
            attempts,
            reports,
            baseline=args.baseline,
            split=args.split,
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"wrote {output} heldout_tasks={report['heldout_task_count']} "
            f"heldout_pass_rate={report['heldout_pass_rate']} "
            f"non_seed_chains={report['non_seed_chain_passed']}/{report['non_seed_chain_count']}"
        )
        return 0

    if args.command == "concrete-estimator-chain-report":
        tasks = load_benchmarks(Path(args.benchmarks))
        reports = tuple(
            dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
        )
        report = build_concrete_estimator_chain_report(tasks, reports, task_id=args.task_id)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"wrote {output} task={report['benchmark_task_id']} "
            f"passed={report['passed']} components={report['component_passed']}/{report['component_count']}"
        )
        return 0

    if args.command == "ablation-report":
        tasks = load_benchmarks(Path(args.benchmarks))
        paper_heldout = json.loads(Path(args.paper_heldout).read_text(encoding="utf-8"))
        concrete_chain_report = json.loads(Path(args.concrete_chain).read_text(encoding="utf-8"))
        training_manifest = json.loads(Path(args.training_manifest).read_text(encoding="utf-8"))
        report = build_ablation_report(
            tasks,
            paper_heldout,
            concrete_chain_report,
            training_manifest,
            tuple(read_jsonl(Path(args.grpo_tasks))),
            tuple(read_jsonl(Path(args.dpo_reports))),
            tuple(read_jsonl(Path(args.lemma_proposal_gates))),
            tuple(read_jsonl(Path(args.lemma_non_vacuity))),
            tuple(read_jsonl(Path(args.lemma_proof_cost))),
            tuple(read_jsonl(Path(args.lemma_ledger))),
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"wrote {output} full_system_ready={report['full_system_ready']} "
            f"components={len(report['components'])} variants={len(report['ablation_rows'])}"
        )
        return 0

    if args.command == "reproducibility-bundle":
        blueprint_data = load_blueprint(Path(args.blueprint))
        errors = validate_blueprint(blueprint_data)
        if errors:
            for error in errors:
                print(f"error: {error}")
            return 1
        artifact_paths = tuple(args.artifacts) if args.artifacts else DEFAULT_REPRODUCIBILITY_ARTIFACTS
        report = build_reproducibility_bundle(
            Path(args.repo_root),
            blueprint_status(blueprint_data),
            artifact_paths=artifact_paths,
            paper_draft_path=args.paper_draft,
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"wrote {output} artifacts={report['artifact_count']} "
            f"all_phases_done={report['all_phases_done']}"
        )
        return 0

    if args.command == "build-lemma-ledger":
        tasks = load_benchmarks(Path(args.benchmarks))
        reports = tuple(
            dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
        )
        entries = build_theorem_hole_lemma_ledger(tasks, reports)
        write_jsonl(Path(args.output), list(entries))
        blocked = sum(1 for entry in entries if entry.status == "blocked_placeholder")
        print(f"ledger_entries={len(entries)} blocked_placeholder={blocked} output={args.output}")
        return 0

    if args.command == "build-lemma-proposals":
        tasks = load_benchmarks(Path(args.benchmarks))
        proposals = build_theorem_hole_lemma_proposals(tasks, proposed_by=args.proposed_by)
        write_jsonl(Path(args.output), list(proposals))
        blocked = sum(1 for proposal in proposals if proposal.blocked_reasons)
        print(f"lemma_proposals={len(proposals)} blocked={blocked} output={args.output}")
        return 0

    if args.command == "theorem-hole-promotion-queue":
        tasks = load_benchmarks(Path(args.benchmarks))
        report = build_theorem_hole_promotion_queue(tasks)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(report) + "\n", encoding="utf-8")
        print(
            f"promotion_queue={report['theorem_hole_task_count']} "
            f"promoted={report['promoted_count']} first_target={report['first_target_task_id']} "
            f"output={args.output}"
        )
        return 0

    if args.command == "check-lemma-proposals":
        proposals = tuple(dataclass_from_dict(LemmaProposal, record) for record in read_jsonl(Path(args.proposals)))
        if args.premises:
            premises = tuple(dataclass_from_dict(PremiseRecord, record) for record in read_jsonl(Path(args.premises)))
        else:
            premises = build_premise_index(Path(args.root), source_dir=args.source_dir)
        reports = build_lemma_proposal_gate_reports(proposals, premises)
        write_jsonl(Path(args.output), list(reports))
        passed = sum(1 for report in reports if report.passed)
        print(f"proposal_gate_reports={len(reports)} passed={passed} output={args.output}")
        return 0

    if args.command == "check-lemma-non-vacuity":
        proposals = tuple(dataclass_from_dict(LemmaProposal, record) for record in read_jsonl(Path(args.proposals)))
        tasks = load_benchmarks(Path(args.benchmarks))
        reports = tuple(
            dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
        )
        non_vacuity_reports = build_lemma_non_vacuity_reports(proposals, tasks, reports)
        write_jsonl(Path(args.output), list(non_vacuity_reports))
        passed = sum(1 for report in non_vacuity_reports if report.passed)
        print(f"non_vacuity_reports={len(non_vacuity_reports)} passed={passed} output={args.output}")
        return 0

    if args.command == "check-lemma-proof-cost":
        proposals = tuple(dataclass_from_dict(LemmaProposal, record) for record in read_jsonl(Path(args.proposals)))
        tasks = load_benchmarks(Path(args.benchmarks))
        proof_cost_reports = build_lemma_proof_cost_reports(proposals, tasks)
        write_jsonl(Path(args.output), list(proof_cost_reports))
        passed = sum(1 for report in proof_cost_reports if report.passed)
        total_delta = sum(report.proof_cost_delta for report in proof_cost_reports)
        print(
            f"proof_cost_reports={len(proof_cost_reports)} "
            f"passed={passed} total_delta={total_delta} output={args.output}"
        )
        return 0

    if args.command == "index-premises":
        records = build_premise_index(Path(args.root), source_dir=args.source_dir)
        write_jsonl(Path(args.output), list(records))
        print(f"indexed={len(records)} output={args.output}")
        return 0

    if args.command == "search-premises":
        records = tuple(dataclass_from_dict(PremiseRecord, record) for record in read_jsonl(Path(args.index)))
        for premise in search_premises(records, args.query, top_k=args.top_k):
            print(f"{premise.name}\t{premise.kind}\t{premise.module}:{premise.line}")
        return 0

    if args.command == "build-training-manifest":
        tasks = load_benchmarks(Path(args.benchmarks))
        attempts: tuple[ProofAttempt, ...] = ()
        reports: tuple[VerificationReport, ...] = ()
        if args.attempts or args.reports:
            if not args.attempts or not args.reports:
                raise SystemExit("--attempts and --reports must be provided together")
            attempts = tuple(dataclass_from_dict(ProofAttempt, record) for record in read_jsonl(Path(args.attempts)))
            reports = tuple(
                dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.reports))
            )
        if args.rejected_attempts or args.rejected_reports:
            if not args.rejected_attempts or not args.rejected_reports:
                raise SystemExit("--rejected-attempts and --rejected-reports must be provided together")
            attempts = attempts + tuple(
                dataclass_from_dict(ProofAttempt, record) for record in read_jsonl(Path(args.rejected_attempts))
            )
            reports = reports + tuple(
                dataclass_from_dict(VerificationReport, record) for record in read_jsonl(Path(args.rejected_reports))
            )
        manifest = build_training_manifest(
            tasks,
            attempts,
            reports,
            run_id=args.run_id,
            base_model=args.base_model,
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(dumps_json(manifest) + "\n", encoding="utf-8")
        print(f"wrote {output}")
        return 0

    if args.command == "materialize-dpo-rejections":
        tasks = load_benchmarks(Path(args.benchmarks))
        attempts = build_rejected_dpo_attempts(tasks, agent_key=args.agent_key)
        write_jsonl(Path(args.output), list(attempts))
        print(f"materialized={len(attempts)} output={args.output}")
        return 0

    if args.command == "materialize-grpo-tasks":
        tasks = load_benchmarks(Path(args.benchmarks))
        process_tasks = build_grpo_process_tasks(
            tasks,
            benchmark_path=args.benchmarks,
            repo=args.repo,
            timeout=args.timeout,
            python=args.python,
        )
        write_jsonl(Path(args.output), list(process_tasks))
        allowed_placeholder_tasks = sum(1 for task in process_tasks if task.allowed_placeholders)
        print(
            f"materialized={len(process_tasks)} "
            f"allowed_placeholder_tasks={allowed_placeholder_tasks} output={args.output}"
        )
        return 0

    if args.command == "assign-worktree":
        agent = get_agent(args.agent)
        manager = WorktreeManager(Path(args.repo))
        assignment = manager.create(agent, base_branch=args.base, dry_run=args.dry_run)
        print(f"agent={assignment.agent_key}")
        print(f"branch={assignment.branch}")
        print(f"path={assignment.path}")
        print(f"owns={','.join(assignment.owns)}")
        print(f"dry_run={assignment.dry_run}")
        return 0

    return 2


def _find_task(path: Path, task_id: str):
    tasks = load_benchmarks(path)
    for task in tasks:
        if task.task_id == task_id:
            return task
    raise SystemExit(f"unknown task id: {task_id}")


def _write_optional_json(path: Path | None, payload: dict):
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_json(payload) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
