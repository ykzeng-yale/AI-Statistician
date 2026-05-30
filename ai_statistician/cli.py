from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from .algorithms import audit_algorithm_registry
from .algorithm_repair_promotion import export_algorithm_repair_promotion_queue
from .algorithm_repair_sandbox import evaluate_algorithm_repair_sandbox
from .algorithm_repair_sandbox_apply import apply_algorithm_repair_sandbox_results
from .algorithm_repair_sandbox_rerun import rerun_algorithm_repair_sandbox_applications
from .architecture_audit import audit_architecture
from .autoform_harness import audit_autoform_harness
from .capability_audit import build_capability_audit, write_capability_audit
from .doctor import build_doctor_report, write_doctor_manifest
from .evaluation import EvalConfig, run_seed_eval
from .autoform_target_export import export_autoform_targets
from .frontier_backlog_audit import audit_frontier_backlog
from .frontier_coverage_audit import audit_frontier_coverage
from .frontier_precision_audit import audit_frontier_precision
from .frontier_smoke_benchmark import FrontierSmokeConfig, run_frontier_smoke_benchmark
from .frontier_theory_target_audit import audit_frontier_theory_targets
from .formal_gap_task_export import export_formal_gap_lean_tasks
from .formalization_target_audit import audit_formalization_targets
from .formal_source_graph import audit_formal_source_graph
from .formal_source_index import audit_formal_source_index
from .intake_audit import audit_question_intake
from .proof_audit import audit_proof_bank
from .proof_bank import all_obligations, obligations_by_tags
from .proof_bank_expansion_export import export_proof_bank_expansion_candidates
from .proof_policy_baseline import evaluate_retrieval_proof_policy_baseline
from .proof_repair_export import export_proof_repair_dataset
from .proof_training_export import export_proof_training_dataset
from .prover_component_audit import build_prover_component_audit, write_prover_component_audit
from .release import ReleaseBundleConfig, build_release_bundle
from .research_evaluation import ResearchEvalConfig, run_research_seed_eval
from .research_gap_audit import audit_research_gap_backlog
from .research_intake_audit import audit_research_question_intake
from .research_knowledge_audit import audit_research_knowledge
from .research_lab import audit_research_algorithm_registry, load_open_research_questions, run_research_benchmark
from .research_loop import LoopConfig, run_research_loop_benchmark
from .research_loop_live_repair_audit import audit_research_loop_live_repair_artifacts
from .research_loop_repair_audit import audit_research_loop_repair_tasks
from .research_next_iteration_audit import audit_next_iteration_queue
from .research_capability_audit import build_research_capability_audit, write_research_capability_audit
from .research_policy_baseline import evaluate_research_policy_baseline
from .research_report import build_research_markdown_report
from .research_system_audit import ResearchSystemAuditConfig, run_research_system_audit
from .research_trace_audit import audit_research_traces
from .research_training_export import export_research_training_dataset
from .questions import QUESTIONS, load_question_file
from .retrieval import audit_proof_bank_retrieval
from .system import AIStatisticianSystem, compact_summary, write_run_manifest, write_trace
from .system_audit import SystemAuditConfig, load_audit_questions, run_system_audit
from .theory_proposal import AnthropicTheoryProposer
from .trace_audit import audit_run_traces
from .verifier import AxleProofVerifier, LocalLeanProofVerifier, MockProofVerifier


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


async def _demo(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    system = (
        AIStatisticianSystem.with_axle(n_runs=args.runs, seed=args.seed)
        if args.real_lean
        else AIStatisticianSystem(n_runs=args.runs, seed=args.seed)
    )
    questions = _questions_from_args(args)
    reports = []
    for question in questions:
        report = await system.run(question)
        reports.append(report)
        if args.out:
            write_trace(report, Path(args.out))
    if args.out:
        write_run_manifest(reports, Path(args.out))

    print("\nAI Statistician System")
    print("=" * 72)
    for report in reports:
        s = compact_summary(report)
        print(
            f"{s['status']:18} {s['question']:24} "
            f"formal={s['formal']:>4} verifier={s['verifier']}"
        )
        print(
            f"  bias={s['bias']:+.5f} rel_bias={s['relative_bias']:+.5f} "
            f"rmse={s['rmse']:.5f} coverage95={s['coverage_95']:.3f}"
        )
        print(f"  sim feedback: {report.simulation.feedback}")
        for proof in report.proofs:
            badge = "OK" if proof.ok else "FAIL"
            print(f"  proof {badge}: {proof.obligation_id} ({proof.elapsed_ms} ms)")
            if proof.errors:
                print(f"    error: {proof.errors[0][:180]}")
        if args.verbose:
            print(f"  estimator: {report.estimator.formula}")
            print(f"  obligations: {', '.join(report.estimator.formal_obligation_ids)}")
    if args.out:
        print(f"\ntraces written to {Path(args.out).resolve()}")
        print(f"manifest written to {(Path(args.out) / 'manifest.json').resolve()}")
    return 0


def _questions_from_args(args: argparse.Namespace):
    proposer = _theory_proposer_from_args(args)
    questions = []
    if args.question_file:
        questions.extend(
            load_question_file(
                Path(args.question_file),
                theory_proposer=proposer,
                force_theory_proposer=bool(getattr(args, "force_llm_theory", False)),
            )
        )
    if getattr(args, "question", None):
        questions.extend(QUESTIONS[question_id] for question_id in args.question)
    if not questions:
        questions.extend(QUESTIONS.values())
    return questions


def _theory_proposer_from_args(args: argparse.Namespace):
    if not getattr(args, "llm_theory", False):
        return None
    return AnthropicTheoryProposer(model=getattr(args, "llm_model", "claude-haiku-4-5"))


def _proof_verifier_from_args(args: argparse.Namespace):
    if getattr(args, "local_lean", False):
        return LocalLeanProofVerifier(
            project_root=getattr(args, "lean_project", None),
            timeout_s=getattr(args, "lean_timeout", 90),
        )
    return AxleProofVerifier() if getattr(args, "real_lean", False) else MockProofVerifier()


async def _eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = _questions_from_args(args)
    if args.seeds:
        seeds = tuple(int(seed) for seed in args.seeds)
    else:
        seeds = tuple(range(args.seed_start, args.seed_start + args.n_seeds))
    payload = await run_seed_eval(
        questions,
        EvalConfig(seeds=seeds, n_runs=args.runs, use_axle=args.real_lean),
        Path(args.out),
    )
    print("\nAI Statistician Evaluation")
    print("=" * 72)
    for question_id, row in payload["summary"].items():
        print(
            f"{question_id:32} accepted={row['accepted']}/{row['trials']} "
            f"rate={row['acceptance_rate']:.2f} "
            f"mean_coverage95={row['mean_coverage_95']:.3f} "
            f"mean_rmse={row['mean_rmse']:.5f}"
        )
    print(f"\nevaluation manifest written to {(Path(args.out) / 'evaluation_manifest.json').resolve()}")
    return 0


def _theory_intake(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = _questions_from_args(args)
    print("\nAI Statistician Theory Intake")
    print("=" * 72)
    for question in questions:
        print(
            f"{question.id:32} dgp_family={question.dgp_family:10} "
            f"estimator_family={question.estimator_family:20} params={question.true_params}"
        )
        proposal_tags = [tag for tag in question.tags if tag.startswith("theory_proposal:")]
        if proposal_tags:
            print(f"  {proposal_tags[0]}")
    return 0


async def _proof_audit(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    payload = await audit_proof_bank(
        verifier,
        Path(args.out),
        ids=args.id,
        tags=args.tag,
        require_all_tags=args.require_all_tags,
        export_lean=not args.no_export_lean,
        export_attempt_log=not args.no_attempt_log,
        include_negative_controls=args.negative_controls,
    )
    print("\nAI Statistician Proof-Bank Audit")
    print("=" * 72)
    print(
        f"verified={payload['n_verified']}/{payload['n_obligations']} "
        f"kernel={payload['n_kernel_verified']}/{payload['n_obligations']} "
        f"verifier={payload['verifier']} strength={payload['verification_strength']}"
    )
    for check in payload["checks"]:
        badge = "OK" if check["ok"] else "FAIL"
        print(f"  proof {badge}: {check['obligation_id']} ({check['elapsed_ms']} ms)")
        if check["errors"]:
            print(f"    error: {check['errors'][0][:180]}")
    print(f"\nproof audit manifest written to {(Path(args.out) / 'proof_audit_manifest.json').resolve()}")
    if payload["lean_export_dir"]:
        print(f"Lean exports written to {Path(str(payload['lean_export_dir'])).resolve()}")
    if payload.get("proof_attempt_log"):
        attempt_log = payload["proof_attempt_log"]
        print(f"proof attempts written to {Path(str(attempt_log['attempt_log'])).resolve()}")
    return 0


def _algorithm_audit(args: argparse.Namespace) -> int:
    payload = audit_algorithm_registry(Path(args.out))
    print("\nAI Statistician Algorithm Audit")
    print("=" * 72)
    print(f"passed={payload['n_ok']}/{payload['n_algorithms']}")
    for row in payload["algorithms"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  algorithm {badge}: {row['algorithm_id']} hash={row['implementation_hash'][:12]}")
        if row["errors"]:
            print(f"    error: {row['errors'][0][:180]}")
    print(f"\nalgorithm audit manifest written to {(Path(args.out) / 'algorithm_audit_manifest.json').resolve()}")
    return 0


def _proof_training_export(args: argparse.Namespace) -> int:
    payload = export_proof_training_dataset(
        Path(args.attempt_log),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistician Proof Training Export")
    print("=" * 72)
    print(
        f"examples={payload['n_sft_examples']} train={payload['n_train']} "
        f"validation={payload['n_validation']} source_attempts={payload['n_attempts']}"
    )
    print(f"train_jsonl={Path(str(payload['train_jsonl'])).resolve()}")
    print(f"validation_jsonl={Path(str(payload['validation_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_training_manifest.json').resolve()}")
    return 0


def _proof_repair_export(args: argparse.Namespace) -> int:
    payload = export_proof_repair_dataset(
        Path(args.attempt_log),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistician Proof Repair Export")
    print("=" * 72)
    print(
        f"repair_examples={payload['n_repair_examples']} "
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"negative_attempts={payload['n_negative_attempts']}"
    )
    print(f"train_jsonl={Path(str(payload['train_jsonl'])).resolve()}")
    print(f"validation_jsonl={Path(str(payload['validation_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_repair_manifest.json').resolve()}")
    return 0


def _proof_policy_baseline(args: argparse.Namespace) -> int:
    payload = evaluate_retrieval_proof_policy_baseline(
        Path(args.train_jsonl),
        Path(args.validation_jsonl),
        Path(args.out),
        k=args.k,
    )
    print("\nAI Statistician Proof Policy Baseline")
    print("=" * 72)
    print(
        f"validation={payload['n_validation']} train={payload['n_train']} "
        f"top1_exact={payload['top1_exact']}/{payload['n_validation']} "
        f"top{payload['k']}_exact={payload['top_k_exact']}/{payload['n_validation']}"
    )
    print(
        f"context_hits={payload['predicted_in_retrieved_context']}/{payload['n_validation']} "
        f"mean_score={payload['mean_top1_score']:.3f}"
    )
    print(f"predictions={Path(str(payload['predictions_jsonl'])).resolve()}")
    print(f"manifest written to {(Path(args.out) / 'proof_policy_baseline_manifest.json').resolve()}")
    return 0


def _research_algorithm_audit(args: argparse.Namespace) -> int:
    payload = audit_research_algorithm_registry(Path(args.out))
    print("\nAI Statistical Theory Lab Algorithm Audit")
    print("=" * 72)
    print(f"passed={payload['n_ok']}/{payload['n_algorithms']}")
    for row in payload["algorithms"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  algorithm {badge}: {row['algorithm_id']} hash={row['implementation_hash'][:12]}")
        for error in row["errors"]:
            print(f"    error: {error[:180]}")
    print(
        f"\nresearch algorithm audit manifest written to "
        f"{(Path(args.out) / 'research_algorithm_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _research_intake_audit(args: argparse.Namespace) -> int:
    supported_files = tuple(Path(path) for path in args.supported_file) if args.supported_file else None
    unsupported_files = tuple(Path(path) for path in args.unsupported_file) if args.unsupported_file else None
    payload = audit_research_question_intake(
        Path(args.out),
        supported_files=supported_files,
        unsupported_files=unsupported_files,
    )
    print("\nAI Statistical Theory Lab Intake Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported_accepted']}/{payload['n_supported']} "
        f"unsupported_rejected={payload['n_unsupported_rejected']}/{payload['n_unsupported']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(
            f"  {badge:4} {row['question_id']} expected={row['expected']} "
            f"class={row['problem_class']}"
        )
        if row["error"]:
            print(f"       {row['error'][:180]}")
    print(
        f"\nresearch intake audit manifest written to "
        f"{(Path(args.out) / 'research_intake_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _frontier_coverage_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_coverage(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Coverage Audit")
    print("=" * 72)
    print(
        f"parsed={payload['n_questions']} supported={payload['n_supported']} "
        f"unsupported={payload['n_unsupported']} rate={payload['supported_rate']:.2f} "
        f"all_ok={payload['all_ok']}"
    )
    for problem_class, count in payload["by_problem_class"].items():
        print(f"  {problem_class}: {count}")
    print(
        f"\nfrontier coverage manifest written to "
        f"{(Path(args.out) / 'frontier_coverage_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_coverage.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_precision_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_precision(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Precision Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported']} body_evidence_ok={payload['n_ok']} "
        f"flagged={payload['n_flagged']} all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        evidence = ", ".join(row["evidence_terms"]) or row["reason"]
        print(f"  {row['ok']}: {row['question_id']} class={row['problem_class']} evidence={evidence}")
    print(f"\nfrontier precision manifest written to {(Path(args.out) / 'frontier_precision_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'frontier_precision.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_backlog_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_backlog(Path(args.out), benchmark_file=Path(args.benchmark_file))
    print("\nAI Statistical Theory Lab Frontier Backlog Audit")
    print("=" * 72)
    print(
        f"backlog={payload['n_ok']}/{payload['n_backlog']} "
        f"domains={len(payload['by_domain'])} all_ok={payload['all_ok']}"
    )
    for domain, count in payload["by_domain"].items():
        print(f"  {domain}: {count}")
    print(f"\nfrontier backlog manifest written to {(Path(args.out) / 'frontier_backlog_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'frontier_backlog.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _frontier_theory_target_audit(args: argparse.Namespace) -> int:
    payload = audit_frontier_theory_targets(
        Path(args.run_dir),
        Path(args.out),
        benchmark_file=Path(args.benchmark_file),
        coverage_threshold=args.coverage_threshold,
    )
    print("\nAI Statistical Theory Lab Frontier Theory Target Audit")
    print("=" * 72)
    print(
        f"scored={payload['n_scored']}/{payload['n_traces']} "
        f"covered={payload['n_covered_results']}/{payload['n_expected_results']} "
        f"rate={payload['expected_result_coverage_rate']:.2f} "
        f"all_scored={payload['all_scored']}"
    )
    for row in payload["rows"]:
        print(
            f"  {row['question_id']}: class={row['problem_class']} "
            f"covered={row['n_covered_results']}/{row['n_expected_results']} "
            f"mean={row['mean_expected_result_coverage']:.2f}"
        )
    print(
        f"\nfrontier theory target manifest written to "
        f"{(Path(args.out) / 'frontier_theory_target_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'frontier_theory_target.md').resolve()}")
    return 0 if payload["all_scored"] else 1


def _research_knowledge_audit(args: argparse.Namespace) -> int:
    payload = audit_research_knowledge(Path(args.out), question_file=Path(args.question_file))
    print("\nAI Statistical Theory Lab Knowledge Audit")
    print("=" * 72)
    print(
        f"sources={payload['n_source_ok']}/{payload['n_cards']} "
        f"inventory={payload['source_inventory']['n_ok']}/{payload['source_inventory']['n_sources']} "
        f"problem_retrieval={payload['n_problem_ok']}/{payload['n_problem_rows']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["problem_rows"]:
        print(
            f"  {row['question_id']}: class={row['problem_class']} "
            f"primary={row['expected_primary']} top={row['top_hit']} "
            f"formal_infra={row['has_formal_infra']}"
        )
    print(
        f"\nresearch knowledge manifest written to "
        f"{(Path(args.out) / 'research_knowledge_audit_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'research_knowledge_audit.md').resolve()}")
    return 0 if payload["all_ok"] else 1


async def _frontier_smoke_benchmark(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    payload = await run_frontier_smoke_benchmark(
        Path(args.out),
        benchmark_file=Path(args.benchmark_file),
        config=FrontierSmokeConfig(
            n_runs=args.runs,
            seed=args.seed,
            max_per_class=args.max_per_class,
            use_axle=args.real_lean,
        ),
        proof_verifier=verifier,
    )
    print("\nAI Statistical Theory Lab Frontier Smoke Benchmark")
    print("=" * 72)
    print(
        f"selected={payload['n_selected']} ready={payload['counts']['ready_with_gaps']}/{payload['counts']['questions']} "
        f"all_gates_passed={payload['all_gates_passed']}"
    )
    for row in payload["selections"]:
        print(f"  {row['question_id']}: class={row['problem_class']} topic={row['topic']}")
    print(f"\nfrontier smoke manifest written to {(Path(args.out) / 'frontier_smoke_manifest.json').resolve()}")
    return 0 if payload["all_gates_passed"] else 1


def _retrieval_audit(args: argparse.Namespace) -> int:
    payload = audit_proof_bank_retrieval(
        Path(args.out),
        k=args.k,
        include_loogle=args.loogle,
        loogle_k=args.loogle_k,
        loogle_timeout_s=args.loogle_timeout,
    )
    print("\nAI Statistician Retrieval Audit")
    print("=" * 72)
    print(
        f"top1={payload['top1']}/{payload['n_obligations']} "
        f"top{payload['k']}={payload['top_k']}/{payload['n_obligations']} "
        f"mrr={payload['mrr']:.3f}"
    )
    for row in payload["rows"]:
        top1 = row["top1"] or "none"
        print(f"  {row['obligation_id']}: rank={row['rank']} top1={top1}")
    if payload["loogle"]["enabled"]:
        loogle = payload["loogle"]
        print(
            f"\nloogle evidence: expected_lemma_hits="
            f"{loogle['n_expected_lemma_hits']}/{loogle['n_queries']} "
            f"errors={loogle['n_errors']}"
        )
        for row in loogle["rows"][:5]:
            status = "HIT" if row["expected_lemma_hit"] else "MISS"
            first = row["hits"][0] if row["hits"] else (row["error"] or "none")
            print(f"  loogle {status}: {row['obligation_id']} first={first}")
    print(f"\nretrieval audit manifest written to {(Path(args.out) / 'retrieval_audit_manifest.json').resolve()}")
    return 0


def _formal_source_audit(args: argparse.Namespace) -> int:
    payload = audit_formal_source_index(Path(args.out), k=args.k, backend=args.backend)
    print("\nAI Statistical Theory Lab Formal Source Index")
    print("=" * 72)
    print(
        f"sources={payload['n_sources']} declarations={payload['n_declarations']} "
        f"queries={payload['n_query_ok']}/{payload['n_queries']} backend={payload['search_backend']}"
    )
    for row in payload["query_rows"]:
        first = row["top_hits"][0] if row["top_hits"] else None
        first_name = first["name"] if first else "none"
        first_source = first["source_id"] if first else "none"
        print(f"  {row['query_id']}: ok={row['ok']} top={first_name} source={first_source}")
    print(
        f"\nformal source index manifest written to "
        f"{(Path(args.out) / 'formal_source_index_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_index.md').resolve()}")
    if payload.get("sqlite_index_path"):
        print(f"sqlite index written to {Path(str(payload['sqlite_index_path'])).resolve()}")
    return 0 if payload["all_queries_ok"] else 1


def _formal_source_graph_audit(args: argparse.Namespace) -> int:
    payload = audit_formal_source_graph(Path(args.out), k=args.k)
    print("\nAI Statistical Theory Lab Formal Source Graph")
    print("=" * 72)
    print(
        f"declarations={payload['n_declarations']} "
        f"symbols={payload['n_symbol_nodes']} edges={payload['n_edges']} "
        f"queries={payload['n_query_ok']}/{payload['n_queries']}"
    )
    for row in payload["query_rows"]:
        first = row["top_hits"][0] if row["top_hits"] else None
        first_name = first["name"] if first else "none"
        first_source = first["source_id"] if first else "none"
        print(f"  {row['query_id']}: ok={row['ok']} top={first_name} source={first_source}")
    print(
        f"\nformal source graph manifest written to "
        f"{(Path(args.out) / 'formal_source_graph_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formal_source_graph.md').resolve()}")
    return 0 if payload["all_queries_ok"] else 1


def _intake_audit(args: argparse.Namespace) -> int:
    supported_files = tuple(Path(path) for path in args.supported_file) if args.supported_file else None
    unsupported_files = tuple(Path(path) for path in args.unsupported_file) if args.unsupported_file else None
    payload = audit_question_intake(
        Path(args.out),
        supported_files=supported_files,
        unsupported_files=unsupported_files,
    )
    print("\nAI Statistician Intake Audit")
    print("=" * 72)
    print(
        f"supported={payload['n_supported_accepted']}/{payload['n_supported']} "
        f"unsupported_rejected={payload['n_unsupported_rejected']}/{payload['n_unsupported']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} expected={row['expected']}")
        if row["error"]:
            print(f"       {row['error'][:180]}")
    print(f"\nintake audit manifest written to {(Path(args.out) / 'intake_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _trace_audit(args: argparse.Namespace) -> int:
    payload = audit_run_traces(Path(args.run_dir), Path(args.out))
    print("\nAI Statistician Trace Audit")
    print("=" * 72)
    print(f"traces={payload['n_ok']}/{payload['n_traces']} all_ok={payload['all_ok']}")
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} {row['trace_path']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(f"\ntrace audit manifest written to {(Path(args.out) / 'trace_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_trace_audit(args: argparse.Namespace) -> int:
    payload = audit_research_traces(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Trace Audit")
    print("=" * 72)
    print(f"traces={payload['n_ok']}/{payload['n_traces']} all_ok={payload['all_ok']}")
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['question_id']} {row['trace_path']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(f"\nresearch trace audit manifest written to {(Path(args.out) / 'research_trace_audit_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_gap_audit(args: argparse.Namespace) -> int:
    payload = audit_research_gap_backlog(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formal Gap Backlog")
    print("=" * 72)
    print(
        f"gaps={payload['n_ok']}/{payload['n_gaps']} "
        f"artifacts={payload['n_artifacts_present']}/{payload['n_gaps']} "
        f"all_ok={payload['all_ok']}"
    )
    for error in payload["manifest_errors"]:
        print(f"  manifest error: {error}")
    for row in payload["rows"]:
        badge = "OK" if row["ok"] else "FAIL"
        print(f"  {badge:4} {row['gap_id']} class={row['problem_class']}")
        for error in row["errors"]:
            print(f"       {error[:180]}")
    print(
        f"\nresearch gap backlog written to "
        f"{(Path(args.out) / 'research_gap_backlog_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'research_gap_backlog.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formalization_target_audit(args: argparse.Namespace) -> int:
    payload = audit_formalization_targets(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formalization Target Queue")
    print("=" * 72)
    print(f"targets={payload['n_ok']}/{payload['n_targets']} all_ok={payload['all_ok']}")
    for row in payload["top_targets"][:10]:
        print(
            f"  {row['priority_band']:24} score={row['priority_score']:4} "
            f"{row['primitive']} gaps={row['n_gaps']}"
        )
        print(f"       bridge: {row['bridge_readiness']}")
        print(f"       next: {row['suggested_next_step'][:180]}")
    print(
        f"\nformalization target manifest written to "
        f"{(Path(args.out) / 'formalization_target_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'formalization_targets.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _formal_gap_task_export(args: argparse.Namespace) -> int:
    payload = export_formal_gap_lean_tasks(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Formal Gap Lean Tasks")
    print("=" * 72)
    print(f"tasks={payload['n_ok']}/{payload['n_tasks']} all_ok={payload['all_ok']}")
    for row in payload["tasks"][:10]:
        print(
            f"  {row['priority_hint']:24} {row['task_id']} "
            f"primitives={len(row['required_primitives'])}"
        )
    print(
        f"\nformal gap task manifest written to "
        f"{(Path(args.out) / 'formal_gap_lean_task_manifest.json').resolve()}"
    )
    print(f"jsonl written to {(Path(args.out) / 'formal_gap_lean_tasks.jsonl').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'formal_gap_lean_tasks.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _autoform_target_export(args: argparse.Namespace) -> int:
    payload = export_autoform_targets(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Autoform Target Export")
    print("=" * 72)
    print(f"targets={payload['n_ok']}/{payload['n_targets']} all_ok={payload['all_ok']}")
    print(f"yaml written to {Path(str(payload['autoform_targets_yaml'])).resolve()}")
    print(f"book dir written to {Path(str(payload['autoform_book_dir'])).resolve()}")
    for command in payload["command_templates"]:
        print(f"  {command}")
    for error in payload["errors"]:
        print(f"  error: {error}")
    return 0 if payload["all_ok"] else 1


def _autoform_harness_audit(args: argparse.Namespace) -> int:
    payload = audit_autoform_harness(Path(args.out))
    profile = payload["profile"]
    print("\nAI Statistical Theory Lab Autoform Harness Audit")
    print("=" * 72)
    print(
        f"ready={payload['ready_for_integration']} "
        f"root={profile['root']} commit={str(profile['git_commit'])[:12]}"
    )
    for key in (
        "has_statement_extraction",
        "has_lean_eval",
        "has_dependency_graph_eval",
        "has_lean_proof_checker",
        "has_lean_repl_tool",
        "has_native_lsp_tool",
        "has_lean_skill_docs",
        "has_multi_agent_bot",
        "has_visualizer",
    ):
        print(f"  {key}: {profile[key]}")
    print(f"\nautoform harness manifest written to {(Path(args.out) / 'autoform_harness_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'autoform_harness.md').resolve()}")
    return 0 if payload["ready_for_integration"] else 1


def _proof_bank_expansion_export(args: argparse.Namespace) -> int:
    payload = export_proof_bank_expansion_candidates(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Proof-Bank Expansion Candidates")
    print("=" * 72)
    print(
        f"candidates={payload['n_ok']}/{payload['n_candidates']} "
        f"bridge_ready={payload['n_bridge_ready']} "
        f"blocked_placeholder={payload['n_blocked_placeholder']} "
        f"all_ok={payload['all_ok']}"
    )
    for row in payload["candidates"][:10]:
        print(
            f"  {row['status']:22} score={row['priority_score']:4} "
            f"{row['primitive']} tasks={len(row['source_task_ids'])}"
        )
    print(
        f"\nproof-bank expansion manifest written to "
        f"{(Path(args.out) / 'proof_bank_expansion_manifest.json').resolve()}"
    )
    print(f"lemma proposals JSONL written to {(Path(args.out) / 'lemma_proposals.jsonl').resolve()}")
    print(
        f"theorem-hole queue written to "
        f"{(Path(args.out) / 'theorem_hole_promotion_queue_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _research_training_export(args: argparse.Namespace) -> int:
    payload = export_research_training_dataset(
        Path(args.run_dir),
        Path(args.out),
        validation_fraction=args.validation_fraction,
        base_model=args.base_model,
    )
    print("\nAI Statistical Theory Lab Research Training Export")
    print("=" * 72)
    print(
        f"traces={payload['n_traces']} sft={payload['n_sft_examples']} "
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"grpo={payload['n_grpo_tasks']} all_ok={payload['all_ok']}"
    )
    for task, count in payload["by_task"].items():
        print(f"  {task}: {count}")
    print(f"\nresearch training manifest written to {(Path(args.out) / 'research_training_manifest.json').resolve()}")
    print(f"train JSONL written to {(Path(args.out) / 'research_sft_train.jsonl').resolve()}")
    print(f"validation JSONL written to {(Path(args.out) / 'research_sft_validation.jsonl').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_policy_baseline(args: argparse.Namespace) -> int:
    payload = evaluate_research_policy_baseline(
        Path(args.train_jsonl),
        Path(args.validation_jsonl),
        Path(args.out),
        k=args.k,
    )
    print("\nAI Statistical Theory Lab Research Policy Baseline")
    print("=" * 72)
    print(
        f"train={payload['n_train']} validation={payload['n_validation']} "
        f"top1_exact={payload['top1_exact_rate']:.3f} "
        f"same_task={payload['same_task_rate']:.3f} "
        f"json_key_f1={payload['mean_json_key_f1']:.3f} "
        f"all_ok={payload['all_ok']}"
    )
    print(f"\nmanifest written to {(Path(args.out) / 'research_policy_baseline_manifest.json').resolve()}")
    print(f"predictions written to {(Path(args.out) / 'research_policy_baseline_predictions.jsonl').resolve()}")
    return 0 if payload["all_ok"] else 1


def _next_iteration_audit(args: argparse.Namespace) -> int:
    payload = audit_next_iteration_queue(Path(args.run_dir), Path(args.out))
    print("\nAI Statistical Theory Lab Next-Iteration Queue")
    print("=" * 72)
    print(
        f"items={payload['n_ok']}/{payload['n_items']} "
        f"actionable={payload['n_actionable_items']} all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_owner"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nnext-iteration queue manifest written to "
        f"{(Path(args.out) / 'next_iteration_queue_manifest.json').resolve()}"
    )
    print(f"markdown report written to {(Path(args.out) / 'next_iteration_queue.md').resolve()}")
    return 0 if payload["all_ok"] else 1


def _research_report(args: argparse.Namespace) -> int:
    payload = build_research_markdown_report(Path(args.run_dir), Path(args.out))
    counts = payload["counts"]
    print("\nAI Statistical Theory Lab Research Report")
    print("=" * 72)
    print(
        f"questions={counts['questions']} ready_with_gaps={counts['ready_with_gaps']} "
        f"proved={counts['proved_subclaims']} gaps={counts['formal_gaps']} "
        f"simulations={counts['simulations_passed']}/{counts['simulations']}"
    )
    for error in payload["errors"]:
        print(f"  report error: {error[:180]}")
    print(f"\nmarkdown report written to {(Path(args.out) / 'research_report.md').resolve()}")
    print(f"report manifest written to {(Path(args.out) / 'research_report_manifest.json').resolve()}")
    return 0 if payload["all_ok"] else 1


def _doctor(args: argparse.Namespace) -> int:
    report = build_doctor_report(
        root=Path(args.root),
        env_file=Path(args.env_file),
        max_manifests=args.max_manifests,
    )
    if args.out:
        manifest = write_doctor_manifest(report, Path(args.out))
    else:
        manifest = None
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        summary = report["summary"]
        print("\nAI Statistician Doctor")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"required_ok={summary['required_ok']}")
        print(f"real_lean_ready={summary['real_lean_ready']}")
        print(f"llm_theory_ready={summary['llm_theory_ready']}")
        print(f"openprover_available={summary['openprover_available']}")
        print(f"registered: obligations={summary['n_obligations']} algorithms={summary['n_algorithms']}")
        for check in report["checks"]:
            required = "required" if check["required"] else "optional"
            print(f"  {check['status']:4} {check['name']} ({required})")
            print(f"       {check['detail']}")
        latest = report["latest_manifests"]
        if latest:
            print("\nlatest manifests")
            for row in latest[: args.max_manifests]:
                print(f"  {row['name']}: {row['path']}")
        if manifest:
            print(f"\ndoctor manifest written to {manifest.resolve()}")
    return 0 if report["summary"]["required_ok"] else 1


def _capability_audit(args: argparse.Namespace) -> int:
    report = build_capability_audit(root=Path(args.root), max_manifests=args.max_manifests)
    manifest = write_capability_audit(report, Path(args.out))
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        print("\nAI Statistician Capability Audit")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"all_required_capabilities_present={report['all_required_capabilities_present']}")
        print(f"ready={report['n_ready']} partial={report['n_partial']} missing={report['n_missing']}")
        for row in report["findings"]:
            print(f"  {row['status']:7} {row['requirement']}")
            for evidence in row["evidence"][:3]:
                print(f"          evidence: {evidence}")
            for limitation in row["limitations"]:
                print(f"          limitation: {limitation}")
        print(f"\ncapability audit manifest written to {manifest.resolve()}")
    return 0 if report["all_required_capabilities_present"] else 1


def _research_capability_audit(args: argparse.Namespace) -> int:
    report = build_research_capability_audit(
        root=Path(args.root),
        question_file=Path(args.question_file),
        frontier_benchmark_file=Path(args.frontier_benchmark_file),
        max_manifests=args.max_manifests,
    )
    manifest = write_research_capability_audit(report, Path(args.out))
    if args.json:
        import json

        print(json.dumps(report, indent=2, default=str))
    else:
        print("\nAI Statistical Theory Lab Capability Audit")
        print("=" * 72)
        print(f"root={report['root']}")
        print(f"goal_complete={report['goal_complete']}")
        print(f"all_current_release_requirements_met={report['all_current_release_requirements_met']}")
        print(
            f"achieved={report['n_achieved']} partial={report['n_partial']} "
            f"not_achieved={report['n_not_achieved']}"
        )
        frontier = report["frontier_summary"]
        print(f"frontier_supported={frontier['n_supported']}/{frontier['n_questions']}")
        for row in report["findings"]:
            gate = "gate" if row["current_release_gate"] else "roadmap"
            print(f"  {row['status']:12} {gate:7} {row['requirement']}")
            for evidence in row["evidence"][:3]:
                print(f"          evidence: {evidence}")
            for limitation in row["limitations"][:2]:
                print(f"          limitation: {limitation}")
        print(f"\nresearch capability audit manifest written to {manifest.resolve()}")
        print(f"markdown report written to {(Path(args.out) / 'research_capability_audit.md').resolve()}")
    return 0 if report["all_current_release_requirements_met"] else 1


def _architecture_audit(args: argparse.Namespace) -> int:
    payload = audit_architecture(Path(args.out))
    print("\nAI Statistician Architecture Audit")
    print("=" * 72)
    print(f"architecture_status={payload['architecture_status']}")
    print(
        "release_scaffold_correct="
        f"{payload['is_current_architecture_correct_for_release_scaffold']}"
    )
    print(
        "full_autonomous_correct="
        f"{payload['is_current_architecture_correct_for_full_autonomous_ai_statistician']}"
    )
    print(f"implemented_feedback_mode={payload['implemented_feedback_mode']}")
    print(f"target_feedback_mode={payload['target_feedback_mode']}")
    for row in payload["components"]:
        print(f"  {row['status']:15} {row['component']}")
    print(f"\narchitecture audit manifest written to {(Path(args.out) / 'architecture_audit_manifest.json').resolve()}")
    print(f"markdown report written to {(Path(args.out) / 'architecture_audit.md').resolve()}")
    return 0 if payload["all_release_scaffold_components_present"] else 1


def _prover_component_audit(args: argparse.Namespace) -> int:
    payload = build_prover_component_audit(
        root=Path(args.root),
        question_file=Path(args.question_file),
        frontier_benchmark_file=Path(args.frontier_benchmark_file),
    )
    manifest, report = write_prover_component_audit(payload, Path(args.out))
    if args.json:
        import json

        print(json.dumps(payload, indent=2, default=str))
    else:
        summary = payload["summary"]
        print("\nAI Statistician Prover Component Audit")
        print("=" * 72)
        print(f"paper_outline_exists={payload['paper_outline_exists']}")
        print(
            f"components={summary['components']} ready={summary['ready']} "
            f"partial={summary['partial']} missing_or_not_trained={summary['missing_or_not_trained']}"
        )
        for row in payload["rows"]:
            print(f"  {row['status']:25} {row['component']}")
            for item in row["missing_or_next"][:2]:
                print(f"          next: {item}")
        print(f"\nprover component audit manifest written to {manifest.resolve()}")
        print(f"markdown report written to {report.resolve()}")
    return 0


async def _system_audit(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_audit_questions(args.question_file, args.include_partial_examples)
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await run_system_audit(
        Path(args.out),
        questions=questions,
        config=SystemAuditConfig(
            n_runs=args.runs,
            seeds=seeds,
            use_axle=args.real_lean,
            include_eval=not args.no_eval,
        ),
    )
    print("\nAI Statistician System Audit")
    print("=" * 72)
    print(f"all_gates_passed={payload['all_gates_passed']}")
    for gate, ok in payload["gates"].items():
        print(f"  {gate}: {'OK' if ok else 'FAIL'}")
    counts = payload["counts"]
    print(
        f"  questions={counts['question_runs_accepted']}/{counts['questions']} "
        f"proofs={counts['proofs_verified']}/{counts['proofs_total']} "
        f"algorithms={counts['algorithms_ok']}/{counts['algorithms_total']}"
    )
    print(f"\nsystem audit manifest written to {(Path(args.out) / 'system_audit_manifest.json').resolve()}")
    return 0


async def _release_bundle(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_audit_questions(args.question_file, args.include_partial_examples)
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await build_release_bundle(
        Path(args.out),
        root=Path(args.root),
        env_file=Path(args.env_file),
        questions=questions,
        config=ReleaseBundleConfig(
            n_runs=args.runs,
            seeds=seeds,
            use_axle=args.real_lean,
            include_eval=not args.no_eval,
            max_manifests=args.max_manifests,
        ),
    )
    print("\nAI Statistician Release Bundle")
    print("=" * 72)
    print(f"release_id={payload['release_id'][:16]}")
    print(f"all_release_gates_passed={payload['all_release_gates_passed']}")
    for gate, ok in payload["gates"].items():
        print(f"  {gate}: {'OK' if ok else 'FAIL'}")
    counts = payload["counts"]
    print(
        f"  questions={counts['question_runs_accepted']}/{counts['questions']} "
        f"proofs={counts['proofs_verified']}/{counts['proofs_total']} "
        f"algorithms={counts['algorithms_ok']}/{counts['algorithms_total']}"
    )
    print(f"\nrelease manifest written to {(Path(args.out) / 'release_manifest.json').resolve()}")
    return 0 if payload["all_release_gates_passed"] else 1


async def _research_benchmark(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    questions = load_open_research_questions(Path(args.question_file))
    payload = await run_research_benchmark(
        questions,
        Path(args.out),
        proof_verifier=verifier,
        formal_source_index_path=(
            Path(args.out) / "formal_source_index.sqlite"
            if args.formal_source_backend == "sqlite"
            else None
        ),
        n_runs=args.runs,
        seed=args.seed,
    )
    print("\nAI Statistical Theory Lab Benchmark")
    print("=" * 72)
    print(
        f"questions={payload['n_questions']} "
        f"ready_with_gaps={payload['n_ready_with_gaps']} "
        f"simulation_flagged={payload['n_simulation_flagged']} "
        f"formal_blocked={payload['n_formal_blocked']}"
    )
    if payload.get("formal_source_search"):
        search = payload["formal_source_search"]
        print(f"formal_source_search={search['backend']}")
        if search.get("sqlite_index_path"):
            print(f"sqlite index written to {Path(str(search['sqlite_index_path'])).resolve()}")
    for row in payload["questions"]:
        formal = row["formal"]
        print(
            f"{row['status']:38} {row['question']:34} "
            f"class={row['problem_class']}"
        )
        print(
            f"  formal: proved={formal['proved']} gaps={formal['gaps']} "
            f"formalized_gaps={formal.get('formalized_gaps', 0)} failed={formal['failed']} "
            f"procedures={', '.join(row['procedures']) or 'none'}"
        )
        for sim in row["simulations"]:
            metrics = sim["metrics"]
            if "coverage_95" in metrics:
                print(
                    f"  sim {sim['procedure_id']}: passed={sim['passed']} "
                    f"coverage95={metrics['coverage_95']:.3f} rmse={metrics.get('rmse', metrics.get('rmse_center', 0.0)):.4f}"
                )
            else:
                print(f"  sim {sim['procedure_id']}: passed={sim['passed']}")
    print(f"\nresearch manifest written to {(Path(args.out) / 'research_benchmark_manifest.json').resolve()}")
    return 0


async def _research_loop(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    verifier = _proof_verifier_from_args(args)
    questions = load_open_research_questions(Path(args.question_file))
    if args.max_questions:
        questions = questions[: args.max_questions]
    payload = await run_research_loop_benchmark(
        questions,
        Path(args.out),
        proof_verifier=verifier,
        formal_source_index_path=(
            Path(args.out) / "formal_source_index.sqlite"
            if args.formal_source_backend == "sqlite"
            else None
        ),
        config=LoopConfig(
            max_rounds=args.max_rounds,
            n_runs=args.runs,
            seed=args.seed,
            mc_rerun_multiplier=args.mc_rerun_multiplier,
        ),
    )
    print("\nAI Statistical Theory Lab Research Loop")
    print("=" * 72)
    print(
        f"questions={payload['n_questions']} max_rounds={payload['config']['max_rounds']} "
        f"all_traces_written={payload['all_loop_traces_written']} "
        f"repair_tasks={payload['n_repair_tasks']}"
    )
    for status, count in payload["status_counts"].items():
        print(f"  {status}: {count}")
    for row in payload["questions"]:
        print(
            f"{row['status']:32} {row['question_id']:34} "
            f"rounds={row['n_rounds']} actions={', '.join(row['action_statuses'])}"
        )
    print(f"\nresearch loop manifest written to {(Path(args.out) / 'research_loop_manifest.json').resolve()}")
    return 0 if payload["all_loop_traces_written"] else 1


def _research_loop_repair_audit(args: argparse.Namespace) -> int:
    payload = audit_research_loop_repair_tasks(
        Path(args.loop_dir),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistical Theory Lab Research Loop Repair Audit")
    print("=" * 72)
    print(
        f"tasks={payload['n_ok']}/{payload['n_tasks']} "
        f"sft={payload['n_sft_examples']} all_ok={payload['all_ok']}"
    )
    for owner, count in payload["by_owner"].items():
        print(f"  {owner}: {count}")
    print(
        f"\nrepair audit manifest written to "
        f"{(Path(args.out) / 'research_loop_repair_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _research_loop_live_repair_audit(args: argparse.Namespace) -> int:
    payload = audit_research_loop_live_repair_artifacts(
        Path(args.loop_dir),
        Path(args.out),
        validation_fraction=args.validation_fraction,
    )
    print("\nAI Statistical Theory Lab Research Loop Live Repair Audit")
    print("=" * 72)
    print(
        f"artifacts={payload['n_ok']}/{payload['n_artifacts']} "
        f"kernel_verified={payload['n_kernel_verified']} "
        f"sft={payload['n_sft_examples']} all_ok={payload['all_ok']}"
    )
    for handler, count in payload["by_handler"].items():
        print(f"  {handler}: {count}")
    print(
        f"\nlive repair audit manifest written to "
        f"{(Path(args.out) / 'research_loop_live_repair_audit_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_promotion(args: argparse.Namespace) -> int:
    payload = export_algorithm_repair_promotion_queue(
        Path(args.loop_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Promotion Queue")
    print("=" * 72)
    print(
        f"algorithm_artifacts={payload['n_algorithm_repair_artifacts']} "
        f"candidates={payload['n_ok']}/{payload['n_candidates']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_sandbox_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nalgorithm repair promotion manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_promotion_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_sandbox(args: argparse.Namespace) -> int:
    payload = evaluate_algorithm_repair_sandbox(
        Path(args.promotion_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Sandbox Evaluation")
    print("=" * 72)
    print(
        f"candidates={payload['n_ok']}/{payload['n_candidates']} "
        f"algorithm_audit_ok={payload['algorithm_audit_all_ok']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_sandbox_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nalgorithm repair sandbox manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_sandbox_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_sandbox_apply(args: argparse.Namespace) -> int:
    payload = apply_algorithm_repair_sandbox_results(
        Path(args.sandbox_dir),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Sandbox Apply Evaluation")
    print("=" * 72)
    print(
        f"applied_artifacts={payload['n_ok']}/{payload['n_candidates']} "
        f"algorithm_audit_ok={payload['algorithm_audit_all_ok']} "
        f"all_ok={payload['all_ok']}"
    )
    for mode, count in payload["by_application_mode"].items():
        print(f"  {mode}: {count}")
    print(
        f"\nalgorithm repair sandbox apply manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_sandbox_apply_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


def _algorithm_repair_sandbox_rerun(args: argparse.Namespace) -> int:
    payload = rerun_algorithm_repair_sandbox_applications(
        Path(args.apply_dir),
        Path(args.out),
        question_file=Path(args.question_file),
        n_runs=args.runs,
        seed=args.seed,
    )
    print("\nAI Statistical Theory Lab Algorithm Repair Sandbox Rerun Evaluation")
    print("=" * 72)
    print(
        f"rerun_artifacts={payload['n_ok']}/{payload['n_candidates']} "
        f"algorithm_audit_ok={payload['algorithm_audit_all_ok']} "
        f"all_ok={payload['all_ok']}"
    )
    for status, count in payload["by_rerun_status"].items():
        print(f"  {status}: {count}")
    print(
        f"\nalgorithm repair sandbox rerun manifest written to "
        f"{(Path(args.out) / 'algorithm_repair_sandbox_rerun_manifest.json').resolve()}"
    )
    return 0 if payload["all_ok"] else 1


async def _research_eval(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    questions = load_open_research_questions(Path(args.question_file))
    seeds = tuple(int(seed) for seed in args.seeds) if args.seeds else tuple(
        range(args.seed_start, args.seed_start + args.n_seeds)
    )
    payload = await run_research_seed_eval(
        questions,
        ResearchEvalConfig(seeds=seeds, n_runs=args.runs, use_axle=args.real_lean),
        Path(args.out),
    )
    print("\nAI Statistical Theory Lab Evaluation")
    print("=" * 72)
    print(
        f"questions={payload['n_questions']} seeds={payload['n_seeds']} "
        f"all_ready_with_gaps={payload['all_ready_with_gaps']} "
        f"trace_audits_ok={payload['all_trace_audits_ok']}"
    )
    for question_id, row in payload["summary"].items():
        print(
            f"{question_id:34} ready={row['ready_with_gaps']}/{row['trials']} "
            f"rate={row['ready_rate']:.2f} "
            f"sim_flagged={row['simulation_flagged']} formal_blocked={row['formal_blocked']}"
        )
        for procedure_id, metrics in row["procedures"].items():
            metric_bits = []
            labels = {
                "coverage_95": "coverage95",
                "rmse": "rmse",
                "rmse_center": "rmse_center",
                "empirical_fdr": "fdr",
                "type1_error": "type1",
                "power": "power",
                "rejection_rate": "rej_rate",
                "alt_mean_stop_time": "alt_stop",
                "null_mean_stop_time": "null_stop",
                "average_width": "avg_width",
                "mean_alignment": "align",
                "mean_subspace_error": "subspace_err",
                "mean_angle_error_rad": "angle_rad",
                "mean_top_eigenvalue": "top_eval",
                "tail_index_rmse": "gamma_rmse",
                "tail_index_coverage_95": "gamma_cov",
                "quantile_relative_bias": "q_rel_bias",
                "quantile_coverage_95": "q_cov",
            }
            for metric_key, label in labels.items():
                value = metrics.get(metric_key, {}).get("mean")
                if value is not None:
                    metric_bits.append(f"{label}={value:.4f}")
            if metric_bits:
                print(f"  {procedure_id}: " + " ".join(metric_bits))
    print(f"\nresearch evaluation manifest written to {(Path(args.out) / 'research_evaluation_manifest.json').resolve()}")
    return 0 if payload["all_trace_audits_ok"] else 1


async def _research_system_audit(args: argparse.Namespace) -> int:
    _load_dotenv(Path(args.env_file))
    payload = await run_research_system_audit(
        Path(args.out),
        question_file=Path(args.question_file),
        config=ResearchSystemAuditConfig(
            n_runs=args.runs,
            seed=args.seed,
            use_axle=args.real_lean,
            use_local_lean=args.local_lean,
            local_lean_project=args.lean_project,
            local_lean_timeout=args.lean_timeout,
        ),
    )
    print("\nAI Statistical Theory Lab System Audit")
    print("=" * 72)
    print(f"all_gates_passed={payload['all_gates_passed']}")
    for gate, ok in payload["gates"].items():
        print(f"  {gate}: {'OK' if ok else 'FAIL'}")
    counts = payload["counts"]
    print(
        f"  questions={counts['research_ready_with_gaps']}/{counts['questions']} "
        f"frontier_supported={counts['frontier_supported']}/{counts['frontier_questions']} "
        f"frontier_precision={counts['frontier_precision_ok']}/{counts['frontier_precision_supported']} "
        f"frontier_backlog={counts['frontier_backlog_ok']}/{counts['frontier_backlog_total']} "
        f"frontier_smoke={counts['frontier_smoke_ready']}/{counts['frontier_smoke_questions']} "
        f"intake_supported={counts['research_intake_supported_accepted']}/{counts['research_intake_supported']} "
        f"intake_unsupported={counts['research_intake_unsupported_rejected']}/{counts['research_intake_unsupported']} "
        f"knowledge={counts['research_knowledge_problem_ok']}/{counts['research_knowledge_problem_rows']} "
        f"sources={counts['research_source_inventory_ok']}/{counts['research_source_inventory_total']} "
        f"algorithms={counts['research_algorithms_ok']}/{counts['research_algorithms_total']} "
        f"proofs={counts['proofs_verified']}/{counts['proofs_total']} "
        f"traces={counts['research_traces_ok']}/{counts['research_traces_total']} "
        f"formalized_gaps={counts['formalized_gaps']}/{counts['formal_gaps']} "
        f"autoform_targets={counts['autoform_targets_ok']}/{counts['autoform_targets_total']} "
        f"gap_backlog={counts['gap_backlog_ok']}/{counts['gap_backlog_total']} "
        f"missing_primitives={counts['missing_formal_primitives']}"
    )
    print(f"\nresearch system audit manifest written to {(Path(args.out) / 'research_system_audit_manifest.json').resolve()}")
    return 0 if payload["all_gates_passed"] else 1


def _list(args: argparse.Namespace) -> int:
    print("Questions")
    for q in QUESTIONS.values():
        print(f"- {q.id}: {q.title}")
    print("\nFormal obligations")
    rows = obligations_by_tags(set(args.tag or [])) if args.tag else all_obligations()
    for obligation in rows:
        print(f"- {obligation.id}: {obligation.title} [{', '.join(obligation.tags)}]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Statistician production core")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="run estimator + formal proof + simulation loop")
    demo.add_argument("--question", action="append", choices=sorted(QUESTIONS), help="run one built-in question; repeatable")
    demo.add_argument("--question-file", help="run one or more external questions from JSON")
    demo.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    demo.add_argument("--llm-theory", action="store_true", help="allow Haiku to classify supported estimator/DGP families during intake")
    demo.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    demo.add_argument("--llm-model", default="claude-haiku-4-5")
    demo.add_argument("--runs", type=int, default=1000, help="Monte Carlo replicates")
    demo.add_argument("--seed", type=int, default=20260528)
    demo.add_argument("--out", default="runs/latest", help="trace output directory")
    demo.add_argument("--env-file", default=".env")
    demo.add_argument("--verbose", action="store_true")
    demo.set_defaults(func=lambda args: asyncio.run(_demo(args)))

    eval_cmd = sub.add_parser("eval", help="run multi-seed evaluation and write an aggregate manifest")
    eval_cmd.add_argument("--question", action="append", choices=sorted(QUESTIONS), help="run one built-in question; repeatable")
    eval_cmd.add_argument("--question-file", help="run one or more external questions from JSON")
    eval_cmd.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    eval_cmd.add_argument("--llm-theory", action="store_true", help="allow Haiku to classify supported estimator/DGP families during intake")
    eval_cmd.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    eval_cmd.add_argument("--llm-model", default="claude-haiku-4-5")
    eval_cmd.add_argument("--runs", type=int, default=500, help="Monte Carlo replicates per trial")
    eval_cmd.add_argument("--n-seeds", type=int, default=3)
    eval_cmd.add_argument("--seed-start", type=int, default=20260528)
    eval_cmd.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    eval_cmd.add_argument("--out", default="runs/eval", help="evaluation output directory")
    eval_cmd.add_argument("--env-file", default=".env")
    eval_cmd.set_defaults(func=lambda args: asyncio.run(_eval(args)))

    proof_audit = sub.add_parser("proof-audit", help="verify the reusable formal proof bank")
    proof_audit.add_argument("--id", action="append", help="specific obligation id; repeatable")
    proof_audit.add_argument("--tag", action="append", help="filter obligations by tag; repeatable")
    proof_audit.add_argument("--require-all-tags", action="store_true", help="require all provided tags instead of any")
    proof_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    proof_audit.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    proof_audit.add_argument("--lean-project", help="local Lake project used by --local-lean")
    proof_audit.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    proof_audit.add_argument("--out", default="runs/proof_audit", help="proof audit output directory")
    proof_audit.add_argument("--env-file", default=".env")
    proof_audit.add_argument("--no-export-lean", action="store_true", help="do not export checked Lean candidates")
    proof_audit.add_argument("--no-attempt-log", action="store_true", help="do not write proof_attempts.jsonl training/audit data")
    proof_audit.add_argument(
        "--negative-controls",
        action="store_true",
        help="also verify one intentionally empty proof body per obligation for repair/value-model data",
    )
    proof_audit.set_defaults(func=lambda args: asyncio.run(_proof_audit(args)))

    proof_training_export = sub.add_parser(
        "proof-training-export",
        help="export verifier-positive proof attempts as whole-proof SFT JSONL data",
    )
    proof_training_export.add_argument(
        "--attempt-log",
        required=True,
        help="path to proof_attempts.jsonl from proof-audit",
    )
    proof_training_export.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="deterministic validation split fraction in [0, 1)",
    )
    proof_training_export.add_argument(
        "--out",
        default="runs/proof_training_export",
        help="output directory for proof_sft_*.jsonl and manifest",
    )
    proof_training_export.set_defaults(func=_proof_training_export)

    proof_repair_export = sub.add_parser(
        "proof-repair-export",
        help="export failed proof attempts paired with accepted proof bodies for repair training",
    )
    proof_repair_export.add_argument(
        "--attempt-log",
        required=True,
        help="path to proof_attempts.jsonl from proof-audit",
    )
    proof_repair_export.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="deterministic validation split fraction in [0, 1)",
    )
    proof_repair_export.add_argument(
        "--out",
        default="runs/proof_repair_export",
        help="output directory for proof_repair_*.jsonl and manifest",
    )
    proof_repair_export.set_defaults(func=_proof_repair_export)

    proof_policy_baseline = sub.add_parser(
        "proof-policy-baseline",
        help="evaluate a nearest-neighbor whole-proof policy over exported SFT data",
    )
    proof_policy_baseline.add_argument("--train-jsonl", required=True, help="proof_sft_train.jsonl")
    proof_policy_baseline.add_argument("--validation-jsonl", required=True, help="proof_sft_validation.jsonl")
    proof_policy_baseline.add_argument("--k", type=int, default=5, help="top-k proof-memory candidates")
    proof_policy_baseline.add_argument(
        "--out",
        default="runs/proof_policy_baseline",
        help="output directory for baseline predictions and manifest",
    )
    proof_policy_baseline.set_defaults(func=_proof_policy_baseline)

    algorithm_audit = sub.add_parser("algorithm-audit", help="audit vetted algorithm implementations")
    algorithm_audit.add_argument("--out", default="runs/algorithm_audit", help="algorithm audit output directory")
    algorithm_audit.set_defaults(func=_algorithm_audit)

    research_algorithm_audit = sub.add_parser(
        "research-algorithm-audit",
        help="audit AI Statistical Theory Lab research procedure implementations",
    )
    research_algorithm_audit.add_argument(
        "--out",
        default="runs/research_algorithm_audit",
        help="research algorithm audit output directory",
    )
    research_algorithm_audit.set_defaults(func=_research_algorithm_audit)

    research_intake_audit = sub.add_parser(
        "research-intake-audit",
        help="audit paper-style research-question normalization and unsupported-topic rejection",
    )
    research_intake_audit.add_argument(
        "--supported-file",
        action="append",
        help="supported research question file; repeatable",
    )
    research_intake_audit.add_argument(
        "--unsupported-file",
        action="append",
        help="unsupported research question file; repeatable",
    )
    research_intake_audit.add_argument(
        "--out",
        default="runs/research_intake_audit",
        help="research intake audit output directory",
    )
    research_intake_audit.set_defaults(func=_research_intake_audit)

    research_knowledge_audit = sub.add_parser(
        "research-knowledge-audit",
        help="audit problem-aware research knowledge retrieval and source locations",
    )
    research_knowledge_audit.add_argument(
        "--question-file",
        default="examples/research_questions.json",
        help="supported research question file used for problem-aware retrieval checks",
    )
    research_knowledge_audit.add_argument(
        "--out",
        default="runs/research_knowledge_audit",
        help="research knowledge audit output directory",
    )
    research_knowledge_audit.set_defaults(func=_research_knowledge_audit)

    frontier_coverage_audit = sub.add_parser(
        "frontier-coverage-audit",
        help="parse the frontier paper benchmark and report deterministic research-lab coverage",
    )
    frontier_coverage_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_coverage_audit.add_argument(
        "--out",
        default="runs/frontier_coverage_audit",
        help="frontier coverage audit output directory",
    )
    frontier_coverage_audit.set_defaults(func=_frontier_coverage_audit)

    frontier_precision_audit = sub.add_parser(
        "frontier-precision-audit",
        help="validate that supported frontier classifications have direct body-text evidence",
    )
    frontier_precision_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_precision_audit.add_argument(
        "--out",
        default="runs/frontier_precision_audit",
        help="frontier precision audit output directory",
    )
    frontier_precision_audit.set_defaults(func=_frontier_precision_audit)

    frontier_backlog_audit = sub.add_parser(
        "frontier-backlog-audit",
        help="cluster unsupported frontier benchmark rows into future theory-roadmap domains",
    )
    frontier_backlog_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_backlog_audit.add_argument(
        "--out",
        default="runs/frontier_backlog_audit",
        help="frontier unsupported-theory backlog output directory",
    )
    frontier_backlog_audit.set_defaults(func=_frontier_backlog_audit)

    frontier_theory_target_audit = sub.add_parser(
        "frontier-theory-target-audit",
        help="score generated frontier traces against withheld expected theoretical results",
    )
    frontier_theory_target_audit.add_argument(
        "--run-dir",
        required=True,
        help="research_benchmark directory containing generated frontier trace JSON files",
    )
    frontier_theory_target_audit.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_theory_target_audit.add_argument(
        "--coverage-threshold",
        type=float,
        default=0.18,
        help="token-coverage threshold for marking one expected result as covered",
    )
    frontier_theory_target_audit.add_argument(
        "--out",
        default="runs/frontier_theory_target_audit",
        help="frontier theory target audit output directory",
    )
    frontier_theory_target_audit.set_defaults(func=_frontier_theory_target_audit)

    frontier_smoke_benchmark = sub.add_parser(
        "frontier-smoke-benchmark",
        help="run full research traces on selected supported entries from the frontier paper benchmark",
    )
    frontier_smoke_benchmark.add_argument(
        "--benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    frontier_smoke_benchmark.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    frontier_smoke_benchmark.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    frontier_smoke_benchmark.add_argument("--lean-project", help="local Lake project used by --local-lean")
    frontier_smoke_benchmark.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    frontier_smoke_benchmark.add_argument("--runs", type=int, default=60, help="Monte Carlo replicates for each selected paper-style question")
    frontier_smoke_benchmark.add_argument("--seed", type=int, default=20260528)
    frontier_smoke_benchmark.add_argument("--max-per-class", type=int, default=1)
    frontier_smoke_benchmark.add_argument("--out", default="runs/frontier_smoke_benchmark", help="frontier smoke output directory")
    frontier_smoke_benchmark.add_argument("--env-file", default=".env")
    frontier_smoke_benchmark.set_defaults(func=lambda args: asyncio.run(_frontier_smoke_benchmark(args)))

    retrieval_audit = sub.add_parser("retrieval-audit", help="audit proof-bank premise retrieval")
    retrieval_audit.add_argument("--k", type=int, default=5, help="top-k threshold")
    retrieval_audit.add_argument("--loogle", action="store_true", help="also record optional Loogle search evidence")
    retrieval_audit.add_argument("--loogle-k", type=int, default=10, help="number of Loogle declarations to keep per query")
    retrieval_audit.add_argument("--loogle-timeout", type=float, default=8.0, help="seconds before a Loogle query is recorded as an error")
    retrieval_audit.add_argument("--out", default="runs/retrieval_audit", help="retrieval audit output directory")
    retrieval_audit.set_defaults(func=_retrieval_audit)

    formal_source_audit = sub.add_parser(
        "formal-source-audit",
        help="index local Lean formal sources and audit theorem-mining queries",
    )
    formal_source_audit.add_argument("--k", type=int, default=8, help="number of declarations to keep per query")
    formal_source_audit.add_argument(
        "--backend",
        choices=("sqlite", "memory"),
        default="sqlite",
        help="retrieval backend for theorem-mining queries",
    )
    formal_source_audit.add_argument(
        "--out",
        default="runs/formal_source_index",
        help="formal source index output directory",
    )
    formal_source_audit.set_defaults(func=_formal_source_audit)

    formal_source_graph_audit = sub.add_parser(
        "formal-source-graph-audit",
        help="audit graph expansion over local Lean/stat declaration symbols",
    )
    formal_source_graph_audit.add_argument("--k", type=int, default=8, help="number of graph-expanded declarations to keep per query")
    formal_source_graph_audit.add_argument(
        "--out",
        default="runs/formal_source_graph",
        help="formal source graph output directory",
    )
    formal_source_graph_audit.set_defaults(func=_formal_source_graph_audit)

    intake_audit = sub.add_parser("intake-audit", help="audit supported question intake and unsupported question rejection")
    intake_audit.add_argument("--supported-file", action="append", help="supported question JSON file; repeatable")
    intake_audit.add_argument("--unsupported-file", action="append", help="unsupported question JSON file; repeatable")
    intake_audit.add_argument("--out", default="runs/intake_audit", help="intake audit output directory")
    intake_audit.set_defaults(func=_intake_audit)

    trace_audit = sub.add_parser("trace-audit", help="validate per-question traces against a run manifest")
    trace_audit.add_argument("--run-dir", required=True, help="directory containing manifest.json and question trace JSON files")
    trace_audit.add_argument("--out", default="runs/trace_audit", help="trace audit output directory")
    trace_audit.set_defaults(func=_trace_audit)

    research_trace_audit = sub.add_parser(
        "research-trace-audit",
        help="validate AI Statistical Theory Lab benchmark traces against their manifest",
    )
    research_trace_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_trace_audit.add_argument(
        "--out",
        default="runs/research_trace_audit",
        help="research trace audit output directory",
    )
    research_trace_audit.set_defaults(func=_research_trace_audit)

    research_gap_audit = sub.add_parser(
        "research-gap-audit",
        help="aggregate and validate FORMAL_GAP records from a research benchmark run",
    )
    research_gap_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_gap_audit.add_argument(
        "--out",
        default="runs/research_gap_backlog",
        help="formal gap backlog output directory",
    )
    research_gap_audit.set_defaults(func=_research_gap_audit)

    formalization_target_audit = sub.add_parser(
        "formalization-target-audit",
        help="rank missing FORMAL_GAP primitives into a Lean theorem-development queue",
    )
    formalization_target_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    formalization_target_audit.add_argument(
        "--out",
        default="runs/formalization_target_audit",
        help="formalization target audit output directory",
    )
    formalization_target_audit.set_defaults(func=_formalization_target_audit)

    formal_gap_task_export = sub.add_parser(
        "formal-gap-task-export",
        help="export FORMAL_GAP skeletons as machine-readable Lean task JSONL",
    )
    formal_gap_task_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    formal_gap_task_export.add_argument(
        "--out",
        default="runs/formal_gap_lean_tasks",
        help="formal gap Lean task output directory",
    )
    formal_gap_task_export.set_defaults(func=_formal_gap_task_export)

    autoform_target_export = sub.add_parser(
        "autoform-target-export",
        help="export FORMAL_GAP tasks as Autoform-Bot-compatible target YAML",
    )
    autoform_target_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    autoform_target_export.add_argument(
        "--out",
        default="runs/autoform_targets",
        help="Autoform target YAML/book output directory",
    )
    autoform_target_export.set_defaults(func=_autoform_target_export)

    autoform_harness_audit = sub.add_parser(
        "autoform-harness-audit",
        help="audit the local Autoform-Bot harness checkout and reusable entrypoints",
    )
    autoform_harness_audit.add_argument(
        "--out",
        default="runs/autoform_harness",
        help="Autoform harness audit output directory",
    )
    autoform_harness_audit.set_defaults(func=_autoform_harness_audit)

    proof_bank_expansion_export = sub.add_parser(
        "proof-bank-expansion-export",
        help="export formal-gap tasks as proof-bank lemma proposals and theorem-hole queue rows",
    )
    proof_bank_expansion_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    proof_bank_expansion_export.add_argument(
        "--out",
        default="runs/proof_bank_expansion",
        help="proof-bank expansion candidate output directory",
    )
    proof_bank_expansion_export.set_defaults(func=_proof_bank_expansion_export)

    research_training_export = sub.add_parser(
        "research-training-export",
        help="export research traces as SFT/GRPO seed data for theory-lab agents",
    )
    research_training_export.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_training_export.add_argument(
        "--validation-fraction",
        type=float,
        default=0.2,
        help="deterministic validation split fraction in [0, 1)",
    )
    research_training_export.add_argument(
        "--base-model",
        default="untrained-trace-export",
        help="base model label recorded in the legacy training manifest",
    )
    research_training_export.add_argument(
        "--out",
        default="runs/research_training_export",
        help="research trace training export output directory",
    )
    research_training_export.set_defaults(func=_research_training_export)

    research_policy_baseline = sub.add_parser(
        "research-policy-baseline",
        help="evaluate a nearest-neighbor baseline over exported research-agent SFT data",
    )
    research_policy_baseline.add_argument("--train-jsonl", required=True, help="research_sft_train.jsonl")
    research_policy_baseline.add_argument("--validation-jsonl", required=True, help="research_sft_validation.jsonl")
    research_policy_baseline.add_argument("--k", type=int, default=5, help="top-k research-memory candidates")
    research_policy_baseline.add_argument(
        "--out",
        default="runs/research_policy_baseline",
        help="output directory for research policy baseline predictions and manifest",
    )
    research_policy_baseline.set_defaults(func=_research_policy_baseline)

    next_iteration_audit = sub.add_parser(
        "next-iteration-audit",
        help="aggregate per-trace next_iteration_agenda items into a run-level agent queue",
    )
    next_iteration_audit.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    next_iteration_audit.add_argument(
        "--out",
        default="runs/next_iteration_queue",
        help="next-iteration queue output directory",
    )
    next_iteration_audit.set_defaults(func=_next_iteration_audit)

    research_report = sub.add_parser(
        "research-report",
        help="write a human-readable Markdown report from persisted AI Statistical Theory Lab traces",
    )
    research_report.add_argument(
        "--run-dir",
        required=True,
        help="directory containing research_benchmark_manifest.json and research trace JSON files",
    )
    research_report.add_argument(
        "--out",
        default="runs/research_report",
        help="research report output directory",
    )
    research_report.set_defaults(func=_research_report)

    doctor = sub.add_parser("doctor", help="inspect local readiness for proof, LLM, retrieval, and audit runs")
    doctor.add_argument("--root", default=".", help="project root to inspect")
    doctor.add_argument("--env-file", default=".env", help="dotenv file to inspect for redacted key presence")
    doctor.add_argument("--out", default="runs/doctor", help="write doctor_manifest.json to this directory")
    doctor.add_argument("--max-manifests", type=int, default=12, help="number of latest run manifests to display")
    doctor.add_argument("--json", action="store_true", help="print machine-readable JSON")
    doctor.set_defaults(func=_doctor)

    capability_audit = sub.add_parser(
        "capability-audit",
        help="map the production objective to current source and manifest evidence",
    )
    capability_audit.add_argument("--root", default=".", help="project root to inspect")
    capability_audit.add_argument("--out", default="runs/capability_audit", help="write capability_audit_manifest.json here")
    capability_audit.add_argument("--max-manifests", type=int, default=12, help="number of recent manifests to include")
    capability_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    capability_audit.set_defaults(func=_capability_audit)

    research_capability_audit = sub.add_parser(
        "research-capability-audit",
        help="map the broad AI Statistical Theory Lab goal to current evidence and honest gaps",
    )
    research_capability_audit.add_argument("--root", default=".", help="project root to inspect")
    research_capability_audit.add_argument("--question-file", default="examples/research_questions.json")
    research_capability_audit.add_argument(
        "--frontier-benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    research_capability_audit.add_argument(
        "--out",
        default="runs/research_capability_audit",
        help="write research_capability_audit_manifest.json here",
    )
    research_capability_audit.add_argument("--max-manifests", type=int, default=12, help="number of recent research manifests to include")
    research_capability_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    research_capability_audit.set_defaults(func=_research_capability_audit)

    architecture_audit = sub.add_parser(
        "architecture-audit",
        help="audit current one-pass scaffold vs target closed-loop AI statistician architecture",
    )
    architecture_audit.add_argument(
        "--out",
        default="runs/architecture_audit",
        help="write architecture_audit_manifest.json here",
    )
    architecture_audit.set_defaults(func=_architecture_audit)

    prover_component_audit = sub.add_parser(
        "prover-component-audit",
        help="audit the system against the modern prover-stack components from the AI-for-math paper outline",
    )
    prover_component_audit.add_argument("--root", default=".", help="project root to inspect")
    prover_component_audit.add_argument("--question-file", default="examples/research_questions.json")
    prover_component_audit.add_argument(
        "--frontier-benchmark-file",
        default="docs/frontier_stat_theory_benchmark.md",
        help="frontier statistical theory benchmark Markdown file",
    )
    prover_component_audit.add_argument(
        "--out",
        default="runs/prover_component_audit",
        help="write prover_component_audit_manifest.json here",
    )
    prover_component_audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    prover_component_audit.set_defaults(func=_prover_component_audit)

    system_audit = sub.add_parser("system-audit", help="run release-style system gates and write one manifest")
    system_audit.add_argument("--question-file", help="additional question JSON file")
    system_audit.add_argument("--include-partial-examples", action="store_true", help="include examples/partial_questions.json")
    system_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof instead of mock verifier")
    system_audit.add_argument("--runs", type=int, default=300, help="Monte Carlo replicates per question")
    system_audit.add_argument("--n-seeds", type=int, default=2)
    system_audit.add_argument("--seed-start", type=int, default=20260528)
    system_audit.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    system_audit.add_argument("--no-eval", action="store_true", help="skip multi-seed evaluation gate")
    system_audit.add_argument("--out", default="runs/system_audit", help="system audit output directory")
    system_audit.add_argument("--env-file", default=".env")
    system_audit.set_defaults(func=lambda args: asyncio.run(_system_audit(args)))

    release_bundle = sub.add_parser("release-bundle", help="write a top-level release manifest from doctor, capability, and system audits")
    release_bundle.add_argument("--root", default=".", help="project root to inspect")
    release_bundle.add_argument("--question-file", help="additional question JSON file")
    release_bundle.add_argument("--include-partial-examples", action="store_true", help="include examples/partial_questions.json")
    release_bundle.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof in the bundled system audit")
    release_bundle.add_argument("--runs", type=int, default=300, help="Monte Carlo replicates per question")
    release_bundle.add_argument("--n-seeds", type=int, default=2)
    release_bundle.add_argument("--seed-start", type=int, default=20260528)
    release_bundle.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    release_bundle.add_argument("--no-eval", action="store_true", help="skip multi-seed evaluation gate inside the bundle")
    release_bundle.add_argument("--max-manifests", type=int, default=12, help="number of recent manifests to include in doctor/capability subreports")
    release_bundle.add_argument("--out", default="runs/release_bundle", help="release bundle output directory")
    release_bundle.add_argument("--env-file", default=".env")
    release_bundle.set_defaults(func=lambda args: asyncio.run(_release_bundle(args)))

    theory_intake = sub.add_parser("theory-intake", help="normalize question JSON through deterministic or LLM-gated theory intake")
    theory_intake.add_argument("--question-file", required=True, help="question JSON file")
    theory_intake.add_argument("--llm-theory", action="store_true", help="allow Haiku to classify supported estimator/DGP families during intake")
    theory_intake.add_argument("--force-llm-theory", action="store_true", help="always ask the LLM for family classification")
    theory_intake.add_argument("--llm-model", default="claude-haiku-4-5")
    theory_intake.add_argument("--env-file", default=".env")
    theory_intake.set_defaults(func=_theory_intake)

    research_benchmark = sub.add_parser(
        "research-benchmark",
        help="run the next-stage open-question statistical theory lab benchmark",
    )
    research_benchmark.add_argument("--question-file", default="examples/research_questions.json")
    research_benchmark.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_benchmark.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    research_benchmark.add_argument("--lean-project", help="local Lake project used by --local-lean")
    research_benchmark.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_benchmark.add_argument("--runs", type=int, default=100, help="Monte Carlo research-simulation replicates")
    research_benchmark.add_argument("--seed", type=int, default=20260528)
    research_benchmark.add_argument(
        "--formal-source-backend",
        choices=("sqlite", "memory"),
        default="sqlite",
        help="formal-gap retrieval backend for local Lean/stat source search",
    )
    research_benchmark.add_argument("--out", default="runs/research_benchmark", help="research trace output directory")
    research_benchmark.add_argument("--env-file", default=".env")
    research_benchmark.set_defaults(func=lambda args: asyncio.run(_research_benchmark(args)))

    research_loop = sub.add_parser(
        "research-loop",
        help="execute bounded live feedback rounds over research traces",
    )
    research_loop.add_argument("--question-file", default="examples/research_questions.json")
    research_loop.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_loop.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    research_loop.add_argument("--lean-project", help="local Lake project used by --local-lean")
    research_loop.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_loop.add_argument("--runs", type=int, default=100, help="initial Monte Carlo research-simulation replicates")
    research_loop.add_argument("--seed", type=int, default=20260528)
    research_loop.add_argument("--max-rounds", type=int, default=2)
    research_loop.add_argument("--mc-rerun-multiplier", type=int, default=3)
    research_loop.add_argument("--max-questions", type=int, default=0, help="optional cap for quick smoke runs")
    research_loop.add_argument(
        "--formal-source-backend",
        choices=("sqlite", "memory"),
        default="sqlite",
        help="formal-gap retrieval backend for local Lean/stat source search",
    )
    research_loop.add_argument("--out", default="runs/research_loop", help="research loop output directory")
    research_loop.add_argument("--env-file", default=".env")
    research_loop.set_defaults(func=lambda args: asyncio.run(_research_loop(args)))

    research_loop_repair_audit = sub.add_parser(
        "research-loop-repair-audit",
        help="audit research-loop repair tasks and export SFT planning examples",
    )
    research_loop_repair_audit.add_argument("--loop-dir", required=True, help="directory containing research_loop_manifest.json")
    research_loop_repair_audit.add_argument(
        "--out",
        default="runs/research_loop_repair_audit",
        help="research loop repair audit output directory",
    )
    research_loop_repair_audit.add_argument("--validation-fraction", type=float, default=0.2)
    research_loop_repair_audit.set_defaults(func=_research_loop_repair_audit)

    research_loop_live_repair_audit = sub.add_parser(
        "research-loop-live-repair-audit",
        help="audit executed live repair artifacts and export SFT execution examples",
    )
    research_loop_live_repair_audit.add_argument(
        "--loop-dir",
        required=True,
        help="directory containing research_loop_manifest.json",
    )
    research_loop_live_repair_audit.add_argument(
        "--out",
        default="runs/research_loop_live_repair_audit",
        help="research loop live repair audit output directory",
    )
    research_loop_live_repair_audit.add_argument("--validation-fraction", type=float, default=0.2)
    research_loop_live_repair_audit.set_defaults(func=_research_loop_live_repair_audit)

    algorithm_repair_promotion = sub.add_parser(
        "algorithm-repair-promotion",
        help="convert algorithm live-repair artifacts into sandbox patch candidates",
    )
    algorithm_repair_promotion.add_argument(
        "--loop-dir",
        required=True,
        help="directory containing research_loop_manifest.json",
    )
    algorithm_repair_promotion.add_argument(
        "--out",
        default="runs/algorithm_repair_promotion",
        help="algorithm repair promotion output directory",
    )
    algorithm_repair_promotion.set_defaults(func=_algorithm_repair_promotion)

    algorithm_repair_sandbox = sub.add_parser(
        "algorithm-repair-sandbox",
        help="evaluate algorithm repair promotion candidates against the current vetted registry",
    )
    algorithm_repair_sandbox.add_argument(
        "--promotion-dir",
        required=True,
        help="directory containing algorithm_repair_promotion_manifest.json",
    )
    algorithm_repair_sandbox.add_argument(
        "--out",
        default="runs/algorithm_repair_sandbox",
        help="algorithm repair sandbox output directory",
    )
    algorithm_repair_sandbox.set_defaults(func=_algorithm_repair_sandbox)

    algorithm_repair_sandbox_apply = sub.add_parser(
        "algorithm-repair-sandbox-apply",
        help="create non-mutating applied sandbox artifacts for ready algorithm repair plans",
    )
    algorithm_repair_sandbox_apply.add_argument(
        "--sandbox-dir",
        required=True,
        help="directory containing algorithm_repair_sandbox_manifest.json",
    )
    algorithm_repair_sandbox_apply.add_argument(
        "--out",
        default="runs/algorithm_repair_sandbox_apply",
        help="algorithm repair sandbox apply output directory",
    )
    algorithm_repair_sandbox_apply.set_defaults(func=_algorithm_repair_sandbox_apply)

    algorithm_repair_sandbox_rerun = sub.add_parser(
        "algorithm-repair-sandbox-rerun",
        help="rerun current vetted simulators for sandbox-applied algorithm repair plans",
    )
    algorithm_repair_sandbox_rerun.add_argument(
        "--apply-dir",
        required=True,
        help="directory containing algorithm_repair_sandbox_apply_manifest.json",
    )
    algorithm_repair_sandbox_rerun.add_argument("--question-file", default="examples/research_questions.json")
    algorithm_repair_sandbox_rerun.add_argument("--runs", type=int, default=50)
    algorithm_repair_sandbox_rerun.add_argument("--seed", type=int, default=20260530)
    algorithm_repair_sandbox_rerun.add_argument(
        "--out",
        default="runs/algorithm_repair_sandbox_rerun",
        help="algorithm repair sandbox rerun output directory",
    )
    algorithm_repair_sandbox_rerun.set_defaults(func=_algorithm_repair_sandbox_rerun)

    research_eval = sub.add_parser(
        "research-eval",
        help="run multi-seed evaluation for the open-question statistical theory lab benchmark",
    )
    research_eval.add_argument("--question-file", default="examples/research_questions.json")
    research_eval.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_eval.add_argument("--runs", type=int, default=80, help="Monte Carlo research-simulation replicates per seed")
    research_eval.add_argument("--n-seeds", type=int, default=3)
    research_eval.add_argument("--seed-start", type=int, default=20260528)
    research_eval.add_argument("--seeds", nargs="*", type=int, help="explicit seeds")
    research_eval.add_argument("--out", default="runs/research_eval", help="research evaluation output directory")
    research_eval.add_argument("--env-file", default=".env")
    research_eval.set_defaults(func=lambda args: asyncio.run(_research_eval(args)))

    research_system_audit = sub.add_parser(
        "research-system-audit",
        help="run release-style gates for the AI Statistical Theory Lab workflow",
    )
    research_system_audit.add_argument("--question-file", default="examples/research_questions.json")
    research_system_audit.add_argument("--real-lean", action="store_true", help="use AXLE verify_proof for Mathlib-backed subclaims")
    research_system_audit.add_argument("--local-lean", action="store_true", help="use local lake env lean kernel verification")
    research_system_audit.add_argument("--lean-project", help="local Lake project used by --local-lean")
    research_system_audit.add_argument("--lean-timeout", type=int, default=90, help="timeout seconds for each local Lean check")
    research_system_audit.add_argument("--runs", type=int, default=100, help="Monte Carlo research-simulation replicates")
    research_system_audit.add_argument("--seed", type=int, default=20260528)
    research_system_audit.add_argument("--out", default="runs/research_system_audit", help="research system audit output directory")
    research_system_audit.add_argument("--env-file", default=".env")
    research_system_audit.set_defaults(func=lambda args: asyncio.run(_research_system_audit(args)))

    list_cmd = sub.add_parser("list", help="list registered questions and formal obligations")
    list_cmd.add_argument("--tag", action="append", help="filter obligations by tag")
    list_cmd.set_defaults(func=_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
