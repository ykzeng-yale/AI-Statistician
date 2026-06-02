from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .formal_source_index import FormalSourceHit, build_formal_source_search_backend


FORMAL_SOURCE_RETRIEVAL_BENCHMARK_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalSourceRetrievalBenchmarkCase:
    query_id: str
    query: str
    expected_name_fragments: tuple[str, ...]
    expected_source_ids: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(frozen=True)
class FormalSourceRetrievalBenchmarkRow:
    query_id: str
    query: str
    expected_name_fragments: tuple[str, ...]
    expected_source_ids: tuple[str, ...]
    hit_rank: int | None
    top1_name: str
    top1_source_id: str
    ok: bool
    top_hits: tuple[dict[str, object], ...]


DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK: tuple[FormalSourceRetrievalBenchmarkCase, ...] = (
    FormalSourceRetrievalBenchmarkCase(
        query_id="variance_sum_independent",
        query="variance finite sum independent pairwise IndepFun variance_sum",
        expected_name_fragments=("IndepFun.variance_sum",),
        expected_source_ids=("mathlib_probability",),
        rationale="finite-sample estimator variance proofs need Mathlib's independent-sum variance theorem",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="finite_union_bound",
        query="finite union bound Bonferroni measure biUnion finset le",
        expected_name_fragments=("measure_biUnion_finset_le",),
        expected_source_ids=("mathlib_measure_theory",),
        rationale="screening and simultaneous coverage proofs need finite union probability control",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="rademacher_subgaussian",
        query="Rademacher sign symmetrization support subGaussian",
        expected_name_fragments=("boolToRademacherSign_hasSubgaussianMGF",),
        expected_source_ids=("empirical_process_lean",),
        rationale="empirical-process symmetrization needs reusable Rademacher/sub-Gaussian support",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="backward_martingale_probability",
        query="backward martingale reverse filtration conditional expectation convergence",
        expected_name_fragments=("martingale_conditional",),
        expected_source_ids=("empirical_process_lean",),
        rationale="optional-stopping and e-process lanes need martingale conditional-expectation sources",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="atlas_subgaussian_mgf",
        query="Atlas HighDimensionalStatistics IsSubGaussian mgf bound Bernstein concentration",
        expected_name_fragments=("IsSubGaussian.mgf_bound",),
        expected_source_ids=("atlas_lean_high_dimensional_statistics",),
        rationale="Atlas high-dimensional statistics should be discoverable as retrieval-only formal context",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="hajek_ratio_identity",
        query="Hajek ratio inverse probability weighting linearization",
        expected_name_fragments=("hajekRatio_eq_populationTarget",),
        expected_source_ids=(
            "empirical_process_lean",
            "legacy_ai_statistician_statinference",
            "local_statinference_repo",
        ),
        rationale="survey/IPW theory revision should recover existing StatInference ratio identities",
    ),
)


EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK: tuple[
    FormalSourceRetrievalBenchmarkCase, ...
] = (
    FormalSourceRetrievalBenchmarkCase(
        query_id="formal_slt_stability_generalization",
        query="turn uniform stability into expected generalization gap for a finite product sample ERM learner",
        expected_name_fragments=("expectedFiniteGeneralizationGap", "uniformStability", "finiteProduct"),
        expected_source_ids=("formal_slt",),
        rationale=(
            "user-intent retrieval should recover FormalSLT stability-to-generalization "
            "bridges without requiring the exact theorem name"
        ),
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="formal_slt_vc_sample_complexity",
        query="PAC VC sample complexity binary classifier Sauer Shelah finite class high probability",
        expected_name_fragments=("genGap_highProb_vcClass",),
        expected_source_ids=("formal_slt",),
        rationale="VC/PAC theorem mining should reuse FormalSLT before inventing new sample-complexity primitives",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="lean_rademacher_dudley_entropy",
        query="Dudley entropy integral upper bound empirical Rademacher complexity covering numbers",
        expected_name_fragments=("dudley_entropy_integral_bound",),
        expected_source_ids=("lean_rademacher",),
        rationale="empirical-process generalization routes should find Dudley/Rademacher source lemmas",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="lean_rademacher_mcdiarmid_uniform_deviation",
        query="bounded differences McDiarmid inequality tail bound empirical uniform deviation",
        expected_name_fragments=("uniform_deviation_tail_bound",),
        expected_source_ids=("lean_rademacher",),
        rationale="finite-sample concentration search should recover McDiarmid-style uniform-deviation bridges",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="lean_machine_learning_ucb_regret",
        query="stochastic bandit UCB algorithm regret pull count upper confidence bound",
        expected_name_fragments=("regret", "pullCount"),
        expected_source_ids=("lean_machine_learning_lml",),
        rationale="algorithmic-statistics routes should mine LML bandit/regret proofs before creating new interfaces",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="brownian_kolmogorov_chentsov",
        query="Brownian motion Gaussian process Kolmogorov Chentsov Holder continuous modification",
        expected_name_fragments=("holderModification",),
        expected_source_ids=("brownian_motion_lean",),
        rationale=(
            "stochastic-process/asymptotic theory planning should find Brownian/Kolmogorov-Chentsov "
            "retrieval-only theorem shapes"
        ),
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="kolmogorov_extension_projective_family",
        query="Kolmogorov extension theorem projective family finite dimensional distributions measure",
        expected_name_fragments=("projectiveFamilyContent",),
        expected_source_ids=("kolmogorov_extension_lean",),
        rationale="process-law construction gaps should discover Kolmogorov extension source lemmas",
    ),
    FormalSourceRetrievalBenchmarkCase(
        query_id="scilean_gaussian_calculus",
        query="Gaussian gradient derivative jacobian optimization calculus SciLean",
        expected_name_fragments=("mul_gaussian_gaussian",),
        expected_source_ids=("scilean_calculus",),
        rationale=(
            "calculus/optimization theorem mining should recover SciLean retrieval-only source context "
            "without exporting WIP code as proof evidence"
        ),
    ),
)


ALL_FORMAL_SOURCE_RETRIEVAL_BENCHMARKS: tuple[FormalSourceRetrievalBenchmarkCase, ...] = (
    DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK
    + EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK
)


def run_formal_source_retrieval_benchmark(
    out_dir: Path | None = None,
    *,
    retriever: object | None = None,
    cases: tuple[FormalSourceRetrievalBenchmarkCase, ...] = DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK,
    k: int = 8,
) -> dict[str, object]:
    """Evaluate gold-family recall for the hybrid Lean/stat source retriever.

    Existing source audits only prove that search returns *some* declarations.
    This benchmark asks a harder question: for representative theorem-mining
    queries, does the retrieval stack recover the intended formal family within
    top-k?  It is still lightweight and local, but it measures premise-selection
    quality rather than mere index liveness.
    """

    active_retriever = retriever or build_formal_source_search_backend()
    rows = [_run_case(active_retriever, case, k=k) for case in cases]
    n_ok = sum(1 for row in rows if row.ok)
    reciprocal_ranks = [1.0 / row.hit_rank for row in rows if row.hit_rank]
    payload: dict[str, object] = {
        "schema_version": FORMAL_SOURCE_RETRIEVAL_BENCHMARK_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "retriever_source": str(getattr(active_retriever, "source", active_retriever.__class__.__name__)),
        "dependency_graph_search": (
            "lean_rag_dependency_graph"
            if getattr(active_retriever, "lean_rag_dependency_graph_enabled", False)
            else ""
        ),
        "lean_rag_dependency_graph_enabled": bool(
            getattr(active_retriever, "lean_rag_dependency_graph_enabled", False)
        ),
        "lean_rag_dependency_graph_path": str(
            getattr(active_retriever, "lean_rag_dependency_graph_path", "")
        ),
        "lean_rag_dependency_graph_auto_discovered": bool(
            getattr(active_retriever, "lean_rag_dependency_graph_auto_discovered", False)
        ),
        "k": int(k),
        "n_cases": len(rows),
        "n_ok": n_ok,
        "all_ok": n_ok == len(rows),
        "recall_at_k": n_ok / len(rows) if rows else 1.0,
        "mean_reciprocal_rank": sum(reciprocal_ranks) / len(rows) if rows else 1.0,
        "rows": [asdict(row) for row in rows],
        "dataset_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "gold-family recall is a retrieval-quality benchmark, not a proof-success theorem",
            "Atlas rows are retrieval-only context and are not exported as training data",
            "the benchmark complements AXLE proof audits; Lean remains the final verifier",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "formal_source_retrieval_benchmark_manifest.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )
        (out_dir / "formal_source_retrieval_benchmark.md").write_text(
            _markdown_report(payload),
            encoding="utf-8",
        )
    return payload


def _run_case(
    retriever: object,
    case: FormalSourceRetrievalBenchmarkCase,
    *,
    k: int,
) -> FormalSourceRetrievalBenchmarkRow:
    hits = list(retriever.search(case.query, k=k)) if hasattr(retriever, "search") else []
    hit_rank = _expected_hit_rank(hits, case)
    top1 = hits[0].declaration if hits else None
    return FormalSourceRetrievalBenchmarkRow(
        query_id=case.query_id,
        query=case.query,
        expected_name_fragments=case.expected_name_fragments,
        expected_source_ids=case.expected_source_ids,
        hit_rank=hit_rank,
        top1_name=top1.name if top1 is not None else "",
        top1_source_id=top1.source_id if top1 is not None else "",
        ok=hit_rank is not None and hit_rank <= k,
        top_hits=tuple(_hit_payload(hit, rank=rank) for rank, hit in enumerate(hits, start=1)),
    )


def _expected_hit_rank(
    hits: list[FormalSourceHit],
    case: FormalSourceRetrievalBenchmarkCase,
) -> int | None:
    for rank, hit in enumerate(hits, start=1):
        decl = hit.declaration
        if case.expected_source_ids and decl.source_id not in case.expected_source_ids:
            continue
        name = decl.name.lower()
        if all(fragment.lower() in name for fragment in case.expected_name_fragments):
            return rank
    return None


def _hit_payload(hit: FormalSourceHit, *, rank: int) -> dict[str, object]:
    decl = hit.declaration
    return {
        "rank": rank,
        "source_id": decl.source_id,
        "path": decl.path,
        "line": decl.line,
        "kind": decl.kind,
        "name": decl.name,
        "score": hit.score,
        "matched_terms": hit.matched_terms,
        "binder_count": decl.binder_count,
        "premise_heads": decl.premise_heads,
        "conclusion_head": decl.conclusion_head,
        "lhs_head": decl.lhs_head,
        "rhs_head": decl.rhs_head,
    }


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Source Retrieval Benchmark",
        "",
        f"- Retriever: `{payload.get('retriever_source')}`",
        f"- Recall@{payload.get('k')}: {payload.get('n_ok')}/{payload.get('n_cases')} "
        f"({float(payload.get('recall_at_k', 0.0)):.3f})",
        f"- MRR: {float(payload.get('mean_reciprocal_rank', 0.0)):.3f}",
        f"- Fingerprint: `{payload.get('dataset_fingerprint')}`",
        "",
        "## Gold Queries",
        "",
        "| Query | OK | Rank | Top hit | Expected name fragments |",
        "|---|---:|---:|---|---|",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        expected = ", ".join(f"`{item}`" for item in row.get("expected_name_fragments", []))
        rank = row.get("hit_rank")
        lines.append(
            f"| `{row.get('query_id')}` | {row.get('ok')} | {rank if rank is not None else 'miss'} | "
            f"`{row.get('top1_name')}` ({row.get('top1_source_id')}) | {expected} |"
        )
    return "\n".join(lines) + "\n"
