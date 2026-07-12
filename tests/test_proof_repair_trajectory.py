from __future__ import annotations

from ai_statistician.fingerprint import stable_hash
from ai_statistician.proof_repair_trajectory import (
    ARTIFACT_KIND,
    build_runtime_lean_proof_repair_trajectory,
    validate_runtime_lean_proof_repair_trajectory,
)


def _fixtures(*, verified: bool):
    target_statement = "theorem exact_source (p : Prop) (hp : p) : p"
    request = {
        "request_fingerprint": "request:abc",
        "target_lean_declaration": "exact_source",
        "target_theorem_statement": target_statement,
        "target_theorem_statement_hash": stable_hash(target_statement),
        "source_lineage_id": "lineage:abc",
        "source_work_order_id": "source:abc",
        "execution_queue_id": "queue:abc",
        "lineage_candidate_artifact_path": "runs/ExactSource.lean",
        "lineage_candidate_artifact_hash": "source-hash",
    }
    work_order = {
        "artifact_kind": "RuntimeExactSourceTheoremProverWorkOrder",
        "work_order_id": "work:abc",
        "question_id": "question:abc",
        "request": request,
    }
    provider = {
        "artifact_kind": "RuntimeOpenProverHLMProofSearchResult",
        "result_id": "provider:abc",
        "provider": "openprover_hlm",
        "status": "DIRECT_CANDIDATE_AVAILABLE",
        "source_theorem_candidate_proof_bodies": ["exact hp"],
        "failure_feedback": [],
    }
    exact = {
        "artifact_kind": "RuntimeExternalExactProofCandidateRerunManifest",
        "manifest_id": "exact:abc",
        "manifest_path": "runs/exact_manifest.json",
        "runtime_verification_contract_satisfied": verified,
        "n_source_theorem_kernel_verified": 1 if verified else 0,
        "rows": [
            {
                "candidate_proof_body_hash": stable_hash("exact hp"),
                "candidate_artifact_path": "runs/candidate.lean",
                "candidate_artifact_hash": "candidate-hash",
                "exact_signature_preserved": True,
                "runtime_owned_local_lean_compiled": verified,
                "source_theorem_kernel_verified": verified,
                "runtime_owned_local_lean_diagnostics": (
                    [] if verified else ["unknown identifier 'missing'"]
                ),
            }
        ],
    }
    return work_order, provider, exact


def test_proof_repair_trajectory_binds_exact_checker_authority() -> None:
    work_order, provider, exact = _fixtures(verified=True)

    trajectory = build_runtime_lean_proof_repair_trajectory(
        work_order=work_order,
        provider_result=provider,
        exact_result=exact,
        lean_project="legacy_sources/emperical_process_lean",
    )

    assert trajectory["artifact_kind"] == ARTIFACT_KIND
    assert trajectory["protocol_source"]["repository"] == (
        "ykzeng-yale/CodexProver"
    )
    assert trajectory["work_order_hash"] == stable_hash(work_order)
    assert trajectory["provider_result_hash"] == stable_hash(provider)
    assert trajectory["exact_candidate_rerun_manifest_hash"] == stable_hash(exact)
    assert trajectory["repair_attempts"][-1]["proof_authority"] is True
    assert trajectory["final_exact_checker_manifest"]["success"] is True
    assert trajectory["authority_boundary"]["mcp_output_can_verify"] is False
    assert trajectory["promotion"]["source_theorem_kernel_verified"] is True
    assert validate_runtime_lean_proof_repair_trajectory(
        trajectory,
        work_order=work_order,
        provider_result=provider,
        exact_result=exact,
    ) == ()


def test_proof_repair_trajectory_rejects_tampered_lineage() -> None:
    work_order, provider, exact = _fixtures(verified=False)
    exact["rows"][0]["runtime_owned_local_lean_compiled"] = True
    exact["rows"][0]["source_theorem_kernel_verified"] = True
    trajectory = build_runtime_lean_proof_repair_trajectory(
        work_order=work_order,
        provider_result=provider,
        exact_result=exact,
    )
    assert trajectory["promotion"]["source_theorem_kernel_verified"] is False
    assert trajectory["repair_attempts"][-1]["failure_class"] == "type_error"
    assert trajectory["repair_attempts"][-1]["proof_authority"] is False

    tampered = dict(trajectory)
    tampered["work_order_hash"] = "changed"
    errors = validate_runtime_lean_proof_repair_trajectory(
        tampered,
        work_order=work_order,
        provider_result=provider,
        exact_result=exact,
    )

    assert "trajectory fingerprint mismatch" in errors
    assert "trajectory work-order hash mismatch" in errors
