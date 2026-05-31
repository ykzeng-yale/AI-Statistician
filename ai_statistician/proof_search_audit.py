from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .proof_bank import all_obligations, proof_bank_fingerprint
from .proof_policy_model import load_proof_policy_model
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
    proof_policy_model_json: Path | None = None,
) -> dict[str, object]:
    """Run a bounded whole-proof search audit over proof-bank obligations."""

    if max_obligations <= 0:
        raise ValueError("max_obligations must be positive")
    if max_nodes <= 0:
        raise ValueError("max_nodes must be positive")
    out_dir.mkdir(parents=True, exist_ok=True)
    proof_verifier = verifier or MockProofVerifier()
    proof_policy_model = load_proof_policy_model(proof_policy_model_json) if proof_policy_model_json else None
    controller = BestFirstWholeProofSearchController(
        proof_verifier,
        proof_policy_model=proof_policy_model,
    )
    obligations = sorted(all_obligations(), key=lambda row: row.id)[:max_obligations]
    results = []
    for obligation in obligations:
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
        results.append(
            await controller.solve(
                obligation,
                max_nodes=max_nodes,
                extra_candidates=probes,
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
    policy_scored_candidates = sum(
        1
        for result in results
        for node in result.nodes
        if node.policy_score is not None
    )
    manifest = {
        "schema_version": PROOF_SEARCH_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "verifier": getattr(proof_verifier, "name", "unknown"),
        "max_obligations": max_obligations,
        "max_nodes": max_nodes,
        "include_invalid_probe": include_invalid_probe,
        "policy_model_enabled": proof_policy_model is not None,
        "policy_model_json": str(proof_policy_model_json) if proof_policy_model_json else "",
        "policy_model_fingerprint": proof_policy_model.model_fingerprint if proof_policy_model else "",
        "n_obligations": n,
        "n_solved": solved,
        "n_failed": n - solved,
        "n_kernel_verified": kernel_verified,
        "all_solved": solved == n,
        "all_kernel_verified_if_verifier_requires_kernel": (
            kernel_verified == solved if "kernel" in getattr(proof_verifier, "name", "").lower() else True
        ),
        "nodes_expanded": nodes_expanded,
        "policy_scored_expanded_nodes": policy_scored_candidates,
        "mean_nodes_expanded": nodes_expanded / n if n else 0.0,
        "results_jsonl": str(results_jsonl),
        "search_audit_fingerprint": stable_hash([asdict(row) for row in results]),
        "limitations": [
            "whole-proof candidate search only; no tactic-state environment yet",
            "best-first candidate priority can use the trained whole-proof policy ranker when a model JSON is supplied",
            "registered proof bodies are included as a high-priority gold skill-memory candidate",
            "invalid_probe is for branch/error-path testing and is disabled in release-style audits",
        ],
    }
    manifest_path = out_dir / "proof_search_audit_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return manifest
