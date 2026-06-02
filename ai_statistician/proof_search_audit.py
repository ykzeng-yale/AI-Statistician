from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .proof_bank import all_obligations, proof_bank_fingerprint
from .proof_policy_model import load_proof_policy_model
from .proof_search_value_model import load_proof_search_value_model
from .retrieval import ProofBankRetriever, query_for_obligation
from .proof_search import (
    PROOF_SEARCH_SCHEMA_VERSION,
    BestFirstWholeProofSearchController,
    ProofCandidate,
)
from .verifier import MockProofVerifier, ProofVerifier


async def audit_proof_search_controller(
    out_dir: Path,
    *,
    verifier: ProofVerifier | None = None,
    max_obligations: int = 12,
    max_nodes: int = 8,
    include_invalid_probe: bool = False,
    include_registered_proof: bool = True,
    proof_policy_model_json: Path | None = None,
    proof_value_model_json: Path | None = None,
    formal_source_retriever: Any | None = None,
    formal_source_k: int = 4,
) -> dict[str, object]:
    """Run a bounded whole-proof search audit over proof-bank obligations."""

    if max_obligations <= 0:
        raise ValueError("max_obligations must be positive")
    if max_nodes <= 0:
        raise ValueError("max_nodes must be positive")
    if formal_source_k < 0:
        raise ValueError("formal_source_k must be nonnegative")
    out_dir.mkdir(parents=True, exist_ok=True)
    proof_verifier = verifier or MockProofVerifier()
    proof_policy_model = load_proof_policy_model(proof_policy_model_json) if proof_policy_model_json else None
    proof_value_model = (
        load_proof_search_value_model(proof_value_model_json)
        if proof_value_model_json
        else None
    )
    controller = BestFirstWholeProofSearchController(
        proof_verifier,
        proof_policy_model=proof_policy_model,
        proof_value_model=proof_value_model,
    )
    retriever = ProofBankRetriever()
    obligations = sorted(all_obligations(), key=lambda row: row.id)[:max_obligations]
    results = []
    for obligation in obligations:
        retrieval_hits = retriever.retrieve(query_for_obligation(obligation), k=8)
        probes = []
        if include_invalid_probe:
            probes.append(
                ProofCandidate(
                    candidate_id=f"{obligation.id}:invalid_probe",
                    proof_body="by\n  sorry",
                    source="invalid_probe",
                    score=1500.0,
                )
            )
        probes.extend(
            _formal_source_candidates(
                obligation,
                formal_source_retriever=formal_source_retriever,
                k=formal_source_k,
            )
        )
        results.append(
            await controller.solve(
                obligation,
                max_nodes=max_nodes,
                extra_candidates=probes,
                retrieval_hits=retrieval_hits,
                include_registered_proof=include_registered_proof,
            )
        )
    results_jsonl = out_dir / "proof_search_results.jsonl"
    with results_jsonl.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(asdict(result), default=str) + "\n")
    n = len(results)
    solved = sum(1 for row in results if row.solved)
    kernel_verified = sum(1 for row in results if row.kernel_verified)
    nodes_expanded = sum(row.nodes_expanded for row in results)
    tactic_template_candidates_total = sum(row.tactic_template_candidates_total for row in results)
    tactic_template_nodes_expanded = sum(
        1
        for result in results
        for node in result.nodes
        if node.source == "builtin_tactic_template"
    )
    policy_scored_candidates = sum(
        1
        for result in results
        for node in result.nodes
        if node.policy_score is not None
    )
    value_scored_candidates = sum(
        1
        for result in results
        for node in result.nodes
        if node.value_score is not None
    )
    retrieval_candidates_total = sum(row.retrieval_candidates_total for row in results)
    formal_source_candidates_total = sum(row.formal_source_candidates_total for row in results)
    retrieval_candidate_nodes_expanded = sum(
        1
        for result in results
        for node in result.nodes
        if node.source.startswith("proof_retrieval:")
    )
    formal_source_candidate_nodes_expanded = sum(
        1
        for result in results
        for node in result.nodes
        if node.source.startswith("formal_source_template:")
    )
    manifest = {
        "schema_version": PROOF_SEARCH_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "verifier": getattr(proof_verifier, "name", "unknown"),
        "max_obligations": max_obligations,
        "max_nodes": max_nodes,
        "include_invalid_probe": include_invalid_probe,
        "include_registered_proof": include_registered_proof,
        "policy_model_enabled": proof_policy_model is not None,
        "policy_model_json": str(proof_policy_model_json) if proof_policy_model_json else "",
        "policy_model_fingerprint": proof_policy_model.model_fingerprint if proof_policy_model else "",
        "value_model_enabled": proof_value_model is not None,
        "value_model_json": str(proof_value_model_json) if proof_value_model_json else "",
        "value_model_fingerprint": proof_value_model.model_fingerprint if proof_value_model else "",
        "formal_source_retriever_enabled": formal_source_retriever is not None,
        "formal_source_k": formal_source_k,
        "n_obligations": n,
        "n_solved": solved,
        "n_failed": n - solved,
        "n_kernel_verified": kernel_verified,
        "all_solved": solved == n,
        "all_kernel_verified_if_verifier_requires_kernel": (
            kernel_verified == solved if "kernel" in getattr(proof_verifier, "name", "").lower() else True
        ),
        "nodes_expanded": nodes_expanded,
        "tactic_template_candidates_total": tactic_template_candidates_total,
        "tactic_template_nodes_expanded": tactic_template_nodes_expanded,
        "retrieval_candidates_total": retrieval_candidates_total,
        "formal_source_candidates_total": formal_source_candidates_total,
        "retrieval_candidate_nodes_expanded": retrieval_candidate_nodes_expanded,
        "formal_source_candidate_nodes_expanded": formal_source_candidate_nodes_expanded,
        "policy_scored_expanded_nodes": policy_scored_candidates,
        "value_scored_expanded_nodes": value_scored_candidates,
        "mean_nodes_expanded": nodes_expanded / n if n else 0.0,
        "results_jsonl": str(results_jsonl),
        "search_audit_fingerprint": stable_hash([asdict(row) for row in results]),
        "limitations": [
            "whole-proof candidate search only; no tactic-state environment yet",
            "built-in tactic templates are one-shot whole-proof bodies, not interactive tactic-state expansion",
            "best-first candidate priority can use trained whole-proof policy and value rankers when model JSON files are supplied",
            "formal-source templates are verifier-tested candidates; source-only declarations may fail if imports/types do not line up",
            (
                "registered proof bodies are included as a high-priority gold skill-memory candidate"
                if include_registered_proof
                else "registered proof bodies are excluded for hard retrieval/search diagnostics"
            ),
            "invalid_probe is for branch/error-path testing and is disabled in release-style audits",
        ],
    }
    manifest_path = out_dir / "proof_search_audit_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest


def _formal_source_candidates(
    obligation,
    *,
    formal_source_retriever: Any | None,
    k: int,
) -> list[ProofCandidate]:
    if formal_source_retriever is None or k <= 0:
        return []
    search = getattr(formal_source_retriever, "search", None)
    if not callable(search):
        return []
    query = " ".join(
        [
            obligation.title,
            obligation.english,
            obligation.formal_statement,
            " ".join(obligation.expected_lemmas),
            " ".join(obligation.tags),
        ]
    )
    hits = search(query, k=k)
    candidates: list[ProofCandidate] = []
    for idx, hit in enumerate(hits):
        decl = getattr(hit, "declaration", None)
        if decl is None:
            continue
        name = _formal_declaration_full_name(decl)
        if not name:
            continue
        source_id = str(getattr(decl, "source_id", "formal_source"))
        score = 80.0 + float(getattr(hit, "score", 0.0) or 0.0) - idx
        candidates.append(
            ProofCandidate(
                candidate_id=f"{obligation.id}:formal_source:{name}:simpa",
                proof_body=f"by\n  simpa using {name}",
                source=f"formal_source_template:{source_id}",
                score=score,
                base_score=score,
                origin_obligation_id=name,
                expected_lemmas=(name,),
                tags=tuple(obligation.tags),
                policy_prompt=str(getattr(decl, "signature", "")),
            )
        )
        candidates.append(
            ProofCandidate(
                candidate_id=f"{obligation.id}:formal_source:{name}:exact",
                proof_body=f"by\n  exact {name}",
                source=f"formal_source_template:{source_id}",
                score=score - 5.0,
                base_score=score - 5.0,
                origin_obligation_id=name,
                expected_lemmas=(name,),
                tags=tuple(obligation.tags),
                policy_prompt=str(getattr(decl, "signature", "")),
            )
        )
    return candidates


def _formal_declaration_full_name(decl: Any) -> str:
    name = str(getattr(decl, "name", "")).strip()
    namespace = str(getattr(decl, "namespace", "")).strip()
    if not name:
        return ""
    if namespace and "." not in name:
        return f"{namespace}.{name}"
    return name
