from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .fingerprint import stable_hash


EVALUATION_BENCHMARK_GUIDANCE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class BenchmarkSuiteGuidanceRow:
    suite_id: str
    exercised: bool
    status: str
    evidence_paths: tuple[str, ...]
    key_counts: dict[str, object]
    honesty_boundary: str
    issues: tuple[str, ...]


def build_evaluation_benchmark_guidance(
    out_dir: Path | None = None,
    *,
    system_audit_payload: Mapping[str, Any],
    strategy_doc: Path = Path("docs/evaluation_benchmark_strategy.md"),
    suites_file: Path = Path("benchmarks/capability_eval_suites.json"),
    frontier_benchmark_file: Path = Path("benchmarks/frontier_stat_theory_benchmark.json"),
    research_questions_file: Path = Path("examples/research_questions.json"),
) -> dict[str, object]:
    """Summarize whether evaluation artifacts guide capacity improvement.

    This audit is intentionally diagnostic. It does not claim the statistical
    theory lab is complete; it turns release/audit counts into a ranked agenda
    for the next capacity improvements and preserves the boundary between
    routing, retrieval, simulation, and Lean proof evidence.
    """

    counts = dict(system_audit_payload.get("counts", {}) or {})
    artifacts = dict(system_audit_payload.get("artifacts", {}) or {})
    gates = dict(system_audit_payload.get("gates", {}) or {})
    suite_config = _read_json(suites_file)
    frontier_config = _read_json(frontier_benchmark_file)
    research_questions = _read_json(research_questions_file)
    strategy_exists = strategy_doc.exists()
    suite_rows = _suite_rows(
        counts=counts,
        artifacts=artifacts,
        gates=gates,
        suites_file=suites_file,
        frontier_benchmark_file=frontier_benchmark_file,
        research_questions_file=research_questions_file,
    )
    stale_rows = [row for row in suite_rows if row.status in {"STALE_OR_MISSING", "UNDER_SPECIFIED"}]
    misaligned_rows = [row for row in suite_rows if row.status in {"SATURATED", "CAPACITY_GAP"}]
    top_actions = _top_actions(suite_rows, counts)
    payload: dict[str, object] = {
        "schema_version": EVALUATION_BENCHMARK_GUIDANCE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "strategy_doc": str(strategy_doc),
        "strategy_doc_present": strategy_exists,
        "suites_file": str(suites_file),
        "suites_defined": len(suite_config.get("suites", [])) if isinstance(suite_config, dict) else 0,
        "frontier_benchmark_file": str(frontier_benchmark_file),
        "frontier_entries": len(frontier_config.get("flat_entries", []))
        if isinstance(frontier_config, dict)
        else 0,
        "research_questions_file": str(research_questions_file),
        "core_research_questions": len(research_questions) if isinstance(research_questions, list) else 0,
        "suites": [asdict(row) for row in suite_rows],
        "n_suites": len(suite_rows),
        "n_exercised": sum(1 for row in suite_rows if row.exercised),
        "n_stale_or_missing": len(stale_rows),
        "n_saturated_or_capacity_gap": len(misaligned_rows),
        "stale_or_missing_suites": tuple(row.suite_id for row in stale_rows),
        "saturated_or_capacity_gap_suites": tuple(row.suite_id for row in misaligned_rows),
        "top_actions": top_actions,
        "all_ok": strategy_exists
        and isinstance(suite_config, dict)
        and len(suite_config.get("suites", [])) >= 9
        and len(suite_rows) >= 9
        and len(top_actions) >= 3,
        "honesty_boundaries": [
            "frontier_supported is routing/scaffold coverage, not solved frontier papers",
            "retrieval/RAG hits are premise suggestions, not Lean proof evidence",
            "simulation diagnostics are empirical evidence, not theorem proofs",
            "formal gaps remain gaps until AXLE/Lean kernel verifies a proof obligation",
        ],
        "guidance_fingerprint": stable_hash(
            {
                "counts": {
                    key: counts.get(key)
                    for key in sorted(counts)
                    if key
                    in {
                        "frontier_questions",
                        "frontier_smoke_questions",
                        "frontier_theory_expected_result_coverage_rate",
                        "formal_gaps",
                        "missing_formal_primitives",
                        "proofs_kernel_verified",
                        "proof_search_kernel_verified",
                        "proof_search_solved",
                        "proof_search_retrieval_ablation_candidate_delta",
                        "proof_search_retrieval_no_registered_ablation_candidate_delta",
                        "proof_search_retrieval_no_registered_ablation_solved_delta",
                        "research_traces_ok",
                        "research_algorithms_ok",
                    }
                },
                "suite_rows": [asdict(row) for row in suite_rows],
                "top_actions": top_actions,
            }
        ),
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "evaluation_benchmark_guidance_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "evaluation_benchmark_guidance.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _suite_rows(
    *,
    counts: Mapping[str, Any],
    artifacts: Mapping[str, Any],
    gates: Mapping[str, Any],
    suites_file: Path,
    frontier_benchmark_file: Path,
    research_questions_file: Path,
) -> tuple[BenchmarkSuiteGuidanceRow, ...]:
    frontier_questions = _int(counts.get("frontier_questions"))
    frontier_smoke_questions = _int(counts.get("frontier_smoke_questions"))
    theory_coverage = _float(counts.get("frontier_theory_expected_result_coverage_rate"))
    missing_primitives = _int(counts.get("missing_formal_primitives"))
    proof_search_candidate_delta = _int(counts.get("proof_search_retrieval_ablation_candidate_delta"))
    proof_search_hard_candidate_delta = _int(
        counts.get("proof_search_retrieval_no_registered_ablation_candidate_delta")
    )
    proof_search_hard_solved_delta = _int(
        counts.get("proof_search_retrieval_no_registered_ablation_solved_delta")
    )
    proofs_kernel_verified = _int(counts.get("proofs_kernel_verified"))
    proof_search_kernel_verified = _int(counts.get("proof_search_kernel_verified"))
    proof_search_solved = _int(counts.get("proof_search_solved"))
    proof_search_obligations = _int(counts.get("proof_search_obligations"))
    algorithm_promotion_ready = _int(counts.get("algorithm_repair_sandbox_patch_eval_promotion_ready"))
    rows = [
        BenchmarkSuiteGuidanceRow(
            suite_id="S0_release_sanity",
            exercised=bool(gates),
            status="OK" if bool(system_gate := gates) and all(bool(v) for v in system_gate.values()) else "CAPACITY_GAP",
            evidence_paths=("research_system_audit_manifest.json",),
            key_counts={
                "all_gates_passed": all(bool(v) for v in gates.values()) if gates else False,
                "proofs_kernel_verified": counts.get("proofs_kernel_verified"),
            },
            honesty_boundary="Release sanity checks scaffold coherence, not autonomous frontier theory discovery.",
            issues=()
            if gates and all(bool(v) for v in gates.values())
            else ("one or more release gates did not pass",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S1_core_method_e2e",
            exercised=bool(artifacts.get("research_benchmark")),
            status="OK"
            if _int(counts.get("research_ready_with_gaps")) == _int(counts.get("questions"))
            and _int(counts.get("research_simulation_flagged")) == 0
            else "CAPACITY_GAP",
            evidence_paths=(str(artifacts.get("research_benchmark", "")), str(research_questions_file)),
            key_counts={
                "questions": counts.get("questions"),
                "ready_with_gaps": counts.get("research_ready_with_gaps"),
                "simulation_flagged": counts.get("research_simulation_flagged"),
            },
            honesty_boundary="Ready-with-gaps means trace completion with explicit gaps, not full theorem closure.",
            issues=()
            if _int(counts.get("research_simulation_flagged")) == 0
            else ("nominal core simulations still have flagged traces",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S2_frontier_static_coverage",
            exercised=bool(artifacts.get("frontier_coverage_audit"))
            and bool(artifacts.get("frontier_precision_audit")),
            status="OK"
            if _int(counts.get("frontier_supported")) == frontier_questions
            and _int(counts.get("frontier_precision_flagged")) == 0
            else "CAPACITY_GAP",
            evidence_paths=(
                str(frontier_benchmark_file),
                str(artifacts.get("frontier_coverage_audit", "")),
                str(artifacts.get("frontier_precision_audit", "")),
            ),
            key_counts={
                "frontier_questions": frontier_questions,
                "frontier_supported": counts.get("frontier_supported"),
                "frontier_precision_flagged": counts.get("frontier_precision_flagged"),
            },
            honesty_boundary="60/60 frontier support is routing and scoped-surrogate coverage only.",
            issues=("static frontier routing is saturated; do not use it as proof of capability",)
            if _int(counts.get("frontier_supported")) == frontier_questions
            else ("frontier routing has unsupported or flagged entries",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S3_frontier_blind_theory_target",
            exercised=bool(artifacts.get("frontier_smoke_benchmark")),
            status="CAPACITY_GAP"
            if frontier_smoke_questions < frontier_questions or theory_coverage < 0.9
            else "OK",
            evidence_paths=(str(artifacts.get("frontier_smoke_benchmark", "")),),
            key_counts={
                "frontier_smoke_questions": frontier_smoke_questions,
                "frontier_questions": frontier_questions,
                "expected_result_coverage_rate": theory_coverage,
            },
            honesty_boundary="Theory-target recovery is semantic planning evidence, not Lean proof evidence.",
            issues=tuple(
                issue
                for issue in (
                    "release smoke is not all-60 frontier scoring"
                    if frontier_smoke_questions < frontier_questions
                    else "",
                    "expected-result coverage remains below the 90% next milestone"
                    if theory_coverage < 0.9
                    else "",
                )
                if issue
            ),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S4_formal_primitive_ladder",
            exercised=bool(artifacts.get("formalization_target_audit"))
            and bool(artifacts.get("proof_bank_expansion")),
            status="CAPACITY_GAP" if missing_primitives > 0 else "OK",
            evidence_paths=(
                str(artifacts.get("formalization_target_audit", "")),
                str(artifacts.get("proof_bank_expansion", "")),
                str(artifacts.get("primitive_source_coverage", "")),
            ),
            key_counts={
                "formal_gaps": counts.get("formal_gaps"),
                "formalized_gaps": counts.get("formalized_gaps"),
                "missing_formal_primitives": missing_primitives,
                "proof_bank_expansion_bridge_ready": counts.get("proof_bank_expansion_bridge_ready"),
                "primitive_source_coverage_direct_wrapper_possible": counts.get(
                    "primitive_source_coverage_direct_wrapper_possible"
                ),
                "primitive_source_coverage_bridge_lemma_needed": counts.get(
                    "primitive_source_coverage_bridge_lemma_needed"
                ),
                "primitive_source_coverage_source_only_not_importable": counts.get(
                    "primitive_source_coverage_source_only_not_importable"
                ),
                "primitive_source_coverage_no_source_found": counts.get(
                    "primitive_source_coverage_no_source_found"
                ),
                "lean_rag_dependency_graph_enabled": counts.get("lean_rag_dependency_graph_enabled"),
                "formal_source_retrieval_ablation_dependency_sensitive_cases": counts.get(
                    "formal_source_retrieval_ablation_dependency_sensitive_cases"
                ),
                "formal_source_retrieval_ablation_dependency_sensitive_new_hits": counts.get(
                    "formal_source_retrieval_ablation_dependency_sensitive_new_hits"
                ),
            },
            honesty_boundary="Formalization targets and skeletons are backlog evidence until kernel-verified.",
            issues=(f"{missing_primitives} missing formal primitives remain",)
            if missing_primitives > 0
            else (),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S5_proof_bank_and_search",
            exercised=bool(artifacts.get("proof_audit"))
            and bool(artifacts.get("proof_search_retrieval_ablation"))
            and bool(artifacts.get("proof_search_retrieval_no_registered_ablation")),
            status=(
                "CAPACITY_GAP"
                if proofs_kernel_verified == 0
                and proof_search_kernel_verified == 0
                and (proof_search_solved > 0 or proof_search_obligations > 0)
                else (
                    "SATURATED"
                    if proof_search_candidate_delta == 0
                    and proof_search_hard_candidate_delta == 0
                    and proof_search_solved == proof_search_obligations
                    else "OK"
                )
            ),
            evidence_paths=(
                str(artifacts.get("proof_audit", "")),
                str(artifacts.get("proof_search_audit", "")),
                str(artifacts.get("proof_search_retrieval_ablation", "")),
                str(artifacts.get("proof_search_retrieval_no_registered_ablation", "")),
            ),
            key_counts={
                "proofs_kernel_verified": proofs_kernel_verified,
                "proof_search_kernel_verified": proof_search_kernel_verified,
                "proof_search_solved": proof_search_solved,
                "proof_search_obligations": proof_search_obligations,
                "proof_search_retrieval_ablation_candidate_delta": proof_search_candidate_delta,
                "proof_search_retrieval_no_registered_ablation_candidate_delta": proof_search_hard_candidate_delta,
                "proof_search_retrieval_no_registered_ablation_solved_delta": proof_search_hard_solved_delta,
                "proof_search_retrieval_no_registered_ablation_include_registered_proof": counts.get(
                    "proof_search_retrieval_no_registered_ablation_include_registered_proof"
                ),
                "lean_rag_dependency_graph_enabled": counts.get("lean_rag_dependency_graph_enabled"),
            },
            honesty_boundary=(
                "Kernel-verified registered obligations are proof evidence; ordinary and no-registered "
                "retrieval ablations are search evidence unless run with AXLE/local Lean verification."
            ),
            issues=tuple(
                issue
                for issue in (
                    "proof-search and proof-bank evidence lacks AXLE/local Lean kernel verification"
                    if proofs_kernel_verified == 0
                    and proof_search_kernel_verified == 0
                    and (proof_search_solved > 0 or proof_search_obligations > 0)
                    else "",
                    "current bounded proof-search suite is saturated; stronger RAG shows no downstream lift"
                    if proof_search_candidate_delta == 0 and proof_search_hard_candidate_delta == 0
                    else "",
                )
                if issue
            ),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S6_algorithm_simulation_stress",
            exercised=bool(artifacts.get("algorithm_simulation_stress_audit")),
            status="OK"
            if bool(counts.get("algorithm_simulation_stress_multi_seed_checked"))
            and bool(counts.get("algorithm_simulation_stress_all_passed"))
            and bool(counts.get("algorithm_simulation_stress_all_finite_metrics"))
            and bool(counts.get("algorithm_simulation_stress_all_stress_ledgers_ok"))
            and bool(counts.get("algorithm_simulation_stress_all_diagnoses_ok"))
            else "UNDER_SPECIFIED",
            evidence_paths=(
                str(artifacts.get("algorithm_simulation_stress_audit", "")),
                str(artifacts.get("research_algorithm_audit", "")),
            ),
            key_counts={
                "research_algorithms_ok": counts.get("research_algorithms_ok"),
                "research_algorithms_total": counts.get("research_algorithms_total"),
                "algorithm_simulation_stress_cases": counts.get("algorithm_simulation_stress_cases"),
                "algorithm_simulation_stress_seeds": counts.get("algorithm_simulation_stress_seeds"),
                "algorithm_simulation_stress_all_passed": counts.get(
                    "algorithm_simulation_stress_all_passed"
                ),
                "algorithm_simulation_stress_all_finite_metrics": counts.get(
                    "algorithm_simulation_stress_all_finite_metrics"
                ),
                "algorithm_simulation_stress_all_stress_ledgers_ok": counts.get(
                    "algorithm_simulation_stress_all_stress_ledgers_ok"
                ),
                "research_report_simulations_passed": counts.get("research_report_simulations_passed"),
                "research_report_simulations": counts.get("research_report_simulations"),
            },
            honesty_boundary="Simulation diagnostics are empirical checks, not guarantees.",
            issues=()
            if bool(counts.get("algorithm_simulation_stress_multi_seed_checked"))
            and bool(counts.get("algorithm_simulation_stress_all_passed"))
            and bool(counts.get("algorithm_simulation_stress_all_finite_metrics"))
            and bool(counts.get("algorithm_simulation_stress_all_stress_ledgers_ok"))
            and bool(counts.get("algorithm_simulation_stress_all_diagnoses_ok"))
            else ("needs passing multi-seed stress ledgers and finite metric checks",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S7_feedback_loop_repair",
            exercised=bool(artifacts.get("research_loop"))
            and bool(artifacts.get("algorithm_repair_sandbox_patch_eval")),
            status="CAPACITY_GAP" if algorithm_promotion_ready == 0 else "OK",
            evidence_paths=(
                str(artifacts.get("research_loop", "")),
                str(artifacts.get("research_loop_repair_audit", "")),
                str(artifacts.get("algorithm_repair_sandbox_patch_eval", "")),
            ),
            key_counts={
                "research_loop_theory_revisions": counts.get("research_loop_theory_revisions"),
                "algorithm_repair_patch_eval_promotion_ready": algorithm_promotion_ready,
                "algorithm_repair_production_patch_applied": counts.get(
                    "algorithm_repair_production_patch_applied"
                ),
            },
            honesty_boundary="Queued or sandboxed repair is not the same as autonomous corrected theory/procedure convergence.",
            issues=("algorithm repair has no promotion-ready patch in the current audit",)
            if algorithm_promotion_ready == 0
            else (),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S8_adversarial_unsupported_intake",
            exercised=bool(artifacts.get("adversarial_intake_audit")),
            status="OK"
            if _int(counts.get("adversarial_intake_cases")) > 0
            and _int(counts.get("adversarial_intake_ok")) == _int(counts.get("adversarial_intake_cases"))
            else "STALE_OR_MISSING",
            evidence_paths=(
                str(artifacts.get("adversarial_intake_audit", "")),
                "benchmarks/adversarial_unsupported_intake.json",
            ),
            key_counts={
                "adversarial_intake_cases": counts.get("adversarial_intake_cases"),
                "adversarial_intake_ok": counts.get("adversarial_intake_ok"),
                "adversarial_intake_rejected": counts.get("adversarial_intake_rejected"),
                "research_intake_unsupported": counts.get("research_intake_unsupported"),
                "research_intake_unsupported_rejected": counts.get("research_intake_unsupported_rejected"),
            },
            honesty_boundary="Unsupported rejection tests protect against overclaiming autonomous capability.",
            issues=()
            if _int(counts.get("adversarial_intake_cases")) > 0
            and _int(counts.get("adversarial_intake_ok")) == _int(counts.get("adversarial_intake_cases"))
            else ("no passing dedicated adversarial/prompt-leakage suite is wired into the release audit",),
        ),
        BenchmarkSuiteGuidanceRow(
            suite_id="S9_fresh_holdout_frontier",
            exercised=bool(artifacts.get("fresh_holdout_frontier_audit")),
            status="OK"
            if bool(counts.get("fresh_holdout_frontier_all_ok"))
            and _int(counts.get("fresh_holdout_frontier_entries")) > 0
            and _int(counts.get("fresh_holdout_frontier_scored_traces")) > 0
            and bool(counts.get("fresh_holdout_frontier_identity_withheld"))
            and not bool(counts.get("fresh_holdout_frontier_source_leakage_detected"))
            else "STALE_OR_MISSING",
            evidence_paths=(
                str(artifacts.get("fresh_holdout_frontier_audit", "")),
                "benchmarks/fresh_holdout_frontier_benchmark.md",
            ),
            key_counts={
                "fresh_holdout_frontier_entries": counts.get("fresh_holdout_frontier_entries"),
                "fresh_holdout_frontier_supported": counts.get("fresh_holdout_frontier_supported"),
                "fresh_holdout_frontier_unsupported": counts.get("fresh_holdout_frontier_unsupported"),
                "fresh_holdout_frontier_scored_traces": counts.get("fresh_holdout_frontier_scored_traces"),
                "fresh_holdout_frontier_expected_results": counts.get(
                    "fresh_holdout_frontier_expected_results"
                ),
                "fresh_holdout_frontier_expected_results_covered": counts.get(
                    "fresh_holdout_frontier_expected_results_covered"
                ),
                "fresh_holdout_frontier_expected_result_coverage_rate": counts.get(
                    "fresh_holdout_frontier_expected_result_coverage_rate"
                ),
                "fresh_holdout_frontier_identity_withheld": counts.get(
                    "fresh_holdout_frontier_identity_withheld"
                ),
                "fresh_holdout_frontier_source_leakage_detected": counts.get(
                    "fresh_holdout_frontier_source_leakage_detected"
                ),
            },
            honesty_boundary="Fresh holdout papers are needed before claiming generalization beyond curated templates.",
            issues=()
            if bool(counts.get("fresh_holdout_frontier_all_ok"))
            and _int(counts.get("fresh_holdout_frontier_entries")) > 0
            and _int(counts.get("fresh_holdout_frontier_scored_traces")) > 0
            and bool(counts.get("fresh_holdout_frontier_identity_withheld"))
            and not bool(counts.get("fresh_holdout_frontier_source_leakage_detected"))
            else ("no passing source-withheld fresh holdout frontier suite is currently present",),
        ),
    ]
    return tuple(rows)


def _top_actions(
    suite_rows: tuple[BenchmarkSuiteGuidanceRow, ...],
    counts: Mapping[str, Any],
) -> list[dict[str, object]]:
    rows_by_id = {row.suite_id: row for row in suite_rows}
    proof_search_frontier_delta = _int(counts.get("proof_search_retrieval_ablation_candidate_delta")) + _int(
        counts.get("proof_search_retrieval_no_registered_ablation_candidate_delta")
    )
    proof_kernel_evidence = _int(counts.get("proofs_kernel_verified")) + _int(
        counts.get("proof_search_kernel_verified")
    )
    actions = [
        {
            "rank": 1,
            "owner_suite": "S4_formal_primitive_ladder",
            "action": "Close or upgrade the top formal primitives into reusable AXLE/Lean proof obligations.",
            "why": f"{_int(counts.get('missing_formal_primitives'))} missing formal primitives remain; this is the main theorem-capacity bottleneck.",
            "success_metric": "missing_formal_primitives decreases or proof_bank_expansion_bridge_ready increases with kernel-verified obligations.",
        },
        {
            "rank": 2,
            "owner_suite": "S3_frontier_blind_theory_target",
            "action": "Run and gate all-60 frontier theory-target scoring with per-topic triage, not only the release smoke subset.",
            "why": "Frontier routing is saturated, but target recovery remains below the next 90% milestone and the smoke set is smaller than the full benchmark.",
            "success_metric": "all-60 expected-result coverage reaches at least 90% while formal gaps remain explicit.",
        },
        {
            "rank": 3,
            "owner_suite": "S5_proof_bank_and_search/S7_feedback_loop_repair",
            "action": (
                "Rerun hard RAG/proof-search candidates through AXLE/local Lean and seed feedback-loop failures where repair must change a decision."
                if proof_kernel_evidence == 0
                else "Add harder RAG/proof-search and seeded feedback-loop failures where stronger retrieval or repair must change a decision."
            ),
            "why": (
                "Search/retrieval artifacts are present, but the current audit has no proof-bank or proof-search kernel evidence; "
                "algorithm repair also has no promotion-ready patch."
                if proof_kernel_evidence == 0
                else (
                    "The current proof-search/RAG ablations still show no candidate-frontier lift and "
                    "algorithm repair has no promotion-ready patch."
                    if proof_search_frontier_delta == 0
                    else (
                        f"Proof-search/RAG hard-mode candidate-frontier lift is {proof_search_frontier_delta}; "
                        "the next bottleneck is turning that search signal into verifier-checked harder obligations, "
                        "while algorithm repair still has no promotion-ready patch."
                    )
                )
            ),
            "success_metric": (
                "proof_search_kernel_verified or proofs_kernel_verified becomes positive under AXLE/local Lean, and at least one seeded simulation/proof failure yields a verified changed trace."
                if proof_kernel_evidence == 0
                else "dependency-graph retrieval improves candidate frontier or solved count on hard obligations, and at least one seeded simulation/proof failure yields a verified changed trace."
            ),
        },
    ]
    if (
        rows_by_id.get("S8_adversarial_unsupported_intake", None) is not None
        and rows_by_id["S8_adversarial_unsupported_intake"].status != "OK"
    ):
        actions.append(
            {
                "rank": 4,
                "owner_suite": "S8_adversarial_unsupported_intake",
                "action": "Wire adversarial unsupported-intake and prompt-leakage cases into the release audit.",
                "why": "The current benchmark stack has no dedicated guardrail suite for vague, contradictory, or gold-leaking frontier prompts.",
                "success_metric": "unsupported/adversarial cases are rejected or scoped without increasing false support claims.",
            }
        )
    return actions[:4]


def _markdown_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Evaluation Benchmark Guidance",
        "",
        f"- Strategy doc present: `{payload.get('strategy_doc_present')}`",
        f"- Suites defined: {payload.get('suites_defined')}",
        f"- Frontier entries: {payload.get('frontier_entries')}",
        f"- Core research questions: {payload.get('core_research_questions')}",
        f"- Exercised suites: {payload.get('n_exercised')}/{payload.get('n_suites')}",
        f"- Stale or missing suites: {payload.get('n_stale_or_missing')}",
        f"- Saturated or capacity-gap suites: {payload.get('n_saturated_or_capacity_gap')}",
        "",
        "## Suite Status",
        "",
        "| Suite | Exercised | Status | Main issue |",
        "|---|---:|---|---|",
    ]
    for row in payload.get("suites", []):
        if not isinstance(row, dict):
            continue
        issues = row.get("issues") or ()
        main_issue = issues[0] if issues else ""
        lines.append(
            f"| `{row.get('suite_id')}` | `{row.get('exercised')}` | `{row.get('status')}` | {main_issue} |"
        )
    lines.extend(["", "## Top Actions", ""])
    for action in payload.get("top_actions", []):
        if not isinstance(action, dict):
            continue
        lines.append(
            f"{action.get('rank')}. **{action.get('owner_suite')}**: {action.get('action')}  \n"
            f"   Why: {action.get('why')}  \n"
            f"   Metric: {action.get('success_metric')}"
        )
    lines.extend(["", "## Honesty Boundaries", ""])
    for boundary in payload.get("honesty_boundaries", []):
        lines.append(f"- {boundary}")
    lines.append("")
    return "\n".join(lines)


def _read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
