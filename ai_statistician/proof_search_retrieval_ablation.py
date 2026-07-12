from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .proof_search_audit import audit_proof_search_controller
from .verifier import ProofVerifier


PROOF_SEARCH_RETRIEVAL_ABLATION_SCHEMA_VERSION = 2


async def run_proof_search_retrieval_ablation(
    out_dir: Path | None = None,
    *,
    baseline_retriever: object | None,
    enhanced_retriever: object | None,
    verifier: ProofVerifier | None = None,
    max_obligations: int = 6,
    max_nodes: int = 4,
    formal_source_k: int = 4,
    include_registered_proof: bool = True,
    baseline_name: str = "proof_search_without_dependency_graph",
    enhanced_name: str = "proof_search_with_dependency_graph",
    legacy_static_template_baseline: bool = False,
) -> dict[str, object]:
    """Measure whether stronger source retrieval changes proof-search frontier.

    This is downstream of the formal-source retrieval benchmark: it runs the
    bounded whole-proof search audit twice and compares solved counts, expanded
    nodes, and formal-source candidate frontier size. It is still an audit over
    candidate generation/search behavior, not a claim that retrieval-only hits
    are Lean proofs.
    """

    if out_dir is None:
        with tempfile.TemporaryDirectory() as tmp:
            return await run_proof_search_retrieval_ablation(
                Path(tmp),
                baseline_retriever=baseline_retriever,
                enhanced_retriever=enhanced_retriever,
                verifier=verifier,
                max_obligations=max_obligations,
                max_nodes=max_nodes,
                formal_source_k=formal_source_k,
                include_registered_proof=include_registered_proof,
                baseline_name=baseline_name,
                enhanced_name=enhanced_name,
                legacy_static_template_baseline=legacy_static_template_baseline,
            )
    baseline_dir = out_dir / "baseline"
    enhanced_dir = out_dir / "enhanced"
    baseline = await audit_proof_search_controller(
        baseline_dir,
        verifier=verifier,
        max_obligations=max_obligations,
        max_nodes=max_nodes,
        formal_source_retriever=baseline_retriever,
        formal_source_k=formal_source_k,
        include_registered_proof=include_registered_proof,
        legacy_static_template_baseline=legacy_static_template_baseline,
    )
    enhanced = await audit_proof_search_controller(
        enhanced_dir,
        verifier=verifier,
        max_obligations=max_obligations,
        max_nodes=max_nodes,
        formal_source_retriever=enhanced_retriever,
        formal_source_k=formal_source_k,
        include_registered_proof=include_registered_proof,
        legacy_static_template_baseline=legacy_static_template_baseline,
    )
    candidate_delta = int(enhanced["formal_source_candidates_total"]) - int(
        baseline["formal_source_candidates_total"]
    )
    expanded_node_delta = int(enhanced["nodes_expanded"]) - int(baseline["nodes_expanded"])
    solved_delta = int(enhanced["n_solved"]) - int(baseline["n_solved"])
    payload: dict[str, object] = {
        "schema_version": PROOF_SEARCH_RETRIEVAL_ABLATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "baseline_name": baseline_name,
        "enhanced_name": enhanced_name,
        "baseline_retriever": _retriever_metadata(baseline_retriever),
        "enhanced_retriever": _retriever_metadata(enhanced_retriever),
        "dependency_graph_search": (
            "lean_rag_dependency_graph"
            if getattr(enhanced_retriever, "lean_rag_dependency_graph_enabled", False)
            else ""
        ),
        "lean_rag_dependency_graph_enabled": bool(
            getattr(enhanced_retriever, "lean_rag_dependency_graph_enabled", False)
        ),
        "lean_rag_dependency_graph_path": str(
            getattr(enhanced_retriever, "lean_rag_dependency_graph_path", "")
        ),
        "lean_rag_dependency_graph_auto_discovered": bool(
            getattr(enhanced_retriever, "lean_rag_dependency_graph_auto_discovered", False)
        ),
        "max_obligations": max_obligations,
        "max_nodes": max_nodes,
        "formal_source_k": formal_source_k,
        "include_registered_proof": include_registered_proof,
        "legacy_static_template_baseline": legacy_static_template_baseline,
        "baseline": _summary(baseline),
        "enhanced": _summary(enhanced),
        "formal_source_candidate_delta": candidate_delta,
        "formal_source_candidate_node_delta": int(enhanced["formal_source_candidate_nodes_expanded"])
        - int(baseline["formal_source_candidate_nodes_expanded"]),
        "nodes_expanded_delta": expanded_node_delta,
        "solved_delta": solved_delta,
        "no_solved_regression": solved_delta >= 0,
        "no_node_expansion_regression": expanded_node_delta <= max_obligations,
        "enhanced_all_solved": bool(enhanced["all_solved"]),
        "saturation_warning": bool(
            include_registered_proof
            and baseline["all_solved"]
            and enhanced["all_solved"]
            and solved_delta == 0
            and candidate_delta == 0
        ),
        "hard_mode_recommendation": (
            "rerun with --no-registered-proof to measure RAG/search lift without the gold proof-bank shortcut"
            if include_registered_proof
            else ""
        ),
        "all_ok": (
            (bool(enhanced["all_solved"]) if include_registered_proof else True)
            and solved_delta >= 0
        ),
        "dataset_fingerprint": stable_hash(
            {
                "baseline": baseline.get("search_audit_fingerprint", ""),
                "enhanced": enhanced.get("search_audit_fingerprint", ""),
                "candidate_delta": candidate_delta,
                "solved_delta": solved_delta,
            }
        ),
        "limitations": [
            "whole-proof best-first search only; not tactic-state proof search",
            (
                "registered proof bodies remain available as skill-memory candidates in this audit"
                if include_registered_proof
                else "registered proof bodies are excluded in this hard diagnostic run"
            ),
            "use include_registered_proof=false for a harder diagnostic that removes the gold proof-bank shortcut",
            "candidate frontier lift is retrieval evidence; only verifier-accepted nodes are proof evidence",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "proof_search_retrieval_ablation_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "proof_search_retrieval_ablation.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )
    return payload


def _summary(payload: dict[str, object]) -> dict[str, object]:
    return {
        "n_obligations": payload.get("n_obligations", 0),
        "n_solved": payload.get("n_solved", 0),
        "nodes_expanded": payload.get("nodes_expanded", 0),
        "mean_nodes_expanded": payload.get("mean_nodes_expanded", 0.0),
        "formal_source_retriever_enabled": payload.get("formal_source_retriever_enabled", False),
        "formal_source_candidates_total": payload.get("formal_source_candidates_total", 0),
        "formal_source_candidate_nodes_expanded": payload.get("formal_source_candidate_nodes_expanded", 0),
        "all_solved": payload.get("all_solved", False),
    }


def _retriever_metadata(retriever: object | None) -> dict[str, object]:
    if retriever is None:
        return {
            "source": "",
            "dependency_graph_search": "",
            "lean_rag_dependency_graph_enabled": False,
            "lean_rag_dependency_graph_path": "",
            "lean_rag_dependency_graph_auto_discovered": False,
        }
    enabled = bool(getattr(retriever, "lean_rag_dependency_graph_enabled", False))
    return {
        "source": str(getattr(retriever, "source", retriever.__class__.__name__)),
        "dependency_graph_search": "lean_rag_dependency_graph" if enabled else "",
        "lean_rag_dependency_graph_enabled": enabled,
        "lean_rag_dependency_graph_path": str(
            getattr(retriever, "lean_rag_dependency_graph_path", "")
        ),
        "lean_rag_dependency_graph_auto_discovered": bool(
            getattr(retriever, "lean_rag_dependency_graph_auto_discovered", False)
        ),
    }


def _markdown_report(payload: dict[str, object]) -> str:
    baseline = payload.get("baseline", {})
    enhanced = payload.get("enhanced", {})
    if not isinstance(baseline, dict):
        baseline = {}
    if not isinstance(enhanced, dict):
        enhanced = {}
    return "\n".join(
        [
            "# Proof Search Retrieval Ablation",
            "",
            f"- Baseline: `{payload.get('baseline_name')}`",
            f"- Enhanced: `{payload.get('enhanced_name')}`",
            f"- Dependency graph search: `{payload.get('dependency_graph_search') or 'disabled'}`",
            f"- Lean RAG enabled: `{payload.get('lean_rag_dependency_graph_enabled')}`",
            f"- Registered proof bodies enabled: `{payload.get('include_registered_proof')}`",
            f"- Enhanced all solved: `{payload.get('enhanced_all_solved')}`",
            f"- Saturation warning: `{payload.get('saturation_warning')}`",
            f"- Solved delta: {payload.get('solved_delta')}",
            f"- Formal-source candidate delta: {payload.get('formal_source_candidate_delta')}",
            f"- Expanded node delta: {payload.get('nodes_expanded_delta')}",
            "",
            "| Metric | Baseline | Enhanced |",
            "|---|---:|---:|",
            f"| solved | {baseline.get('n_solved')} | {enhanced.get('n_solved')} |",
            f"| nodes expanded | {baseline.get('nodes_expanded')} | {enhanced.get('nodes_expanded')} |",
            f"| formal-source candidates | {baseline.get('formal_source_candidates_total')} | {enhanced.get('formal_source_candidates_total')} |",
            f"| formal-source expanded nodes | {baseline.get('formal_source_candidate_nodes_expanded')} | {enhanced.get('formal_source_candidate_nodes_expanded')} |",
            "",
        ]
    )
