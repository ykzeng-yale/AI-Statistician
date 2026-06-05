from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .fingerprint import stable_hash
from .proof_attempt_log import build_proof_attempt_record, write_proof_attempt_log
from .retrieval import ProofBankRetriever, query_for_obligation
from .schema import FormalObligation, ProofCheck
from .verifier import ProofVerifier, splice_proof


STAT_CLAIM_CERTIFICATE_CHECKER_SCHEMA_VERSION = 1
KERNEL_VERIFIED_STATUS = "STAT_CLAIM_CERTIFICATE_CHECKER_KERNEL_VERIFIED"
NOT_KERNEL_VERIFIED_STATUS = "STAT_CLAIM_CERTIFICATE_CHECKER_NOT_KERNEL_VERIFIED"


def _stmt(body: str) -> str:
    return body.strip() + "\n"


CERTIFICATE_CHECKER_OBLIGATIONS: dict[str, FormalObligation] = {
    "conformal_coverage_certificate_sound": FormalObligation(
        id="conformal_coverage_certificate_sound",
        title="Split-conformal coverage certificate checker soundness",
        english=(
            "A conformal coverage certificate packages the measurable bad-rank "
            "event, per-rank probability budgets, and the total budget bound. "
            "If the certificate is accepted, then the complement event has "
            "coverage at least one minus the total budget. This is a small "
            "kernel-checkable certificate theorem for the encoded counting "
            "claim only; it does not prove exchangeability, score ranking, or "
            "paper-level semantic faithfulness."
        ),
        formal_statement=_stmt(
            """
import Mathlib
open MeasureTheory ProbabilityTheory

structure ConformalCoverageCertificate {Ω ρ : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) (BadRanks : Finset ρ) (rank : Ω → ρ)
    (α : ρ → ENNReal) (α_total : ENNReal) : Prop where
  bad_event_measurable : MeasurableSet {ω | rank ω ∈ BadRanks}
  rank_budget : ∀ r ∈ BadRanks, μ {ω | rank ω = r} ≤ α r
  total_budget : (∑ r ∈ BadRanks, α r) ≤ α_total

theorem conformalCoverageCertificate_sound {Ω ρ : Type*}
    [MeasurableSpace Ω]
    (μ : Measure Ω) [IsProbabilityMeasure μ]
    (BadRanks : Finset ρ) (rank : Ω → ρ)
    (α : ρ → ENNReal) (α_total : ENNReal)
    (cert : ConformalCoverageCertificate μ BadRanks rank α α_total) :
    1 - α_total ≤ μ ({ω | rank ω ∈ BadRanks}ᶜ) := by sorry
"""
        ),
        proof_body=(
            "by\n"
            "  rcases cert with ⟨hBadEvent, hRank, h_total⟩\n"
            "  have hbad : μ {ω | rank ω ∈ BadRanks} ≤ α_total := by\n"
            "    calc\n"
            "      μ {ω | rank ω ∈ BadRanks} ≤ μ (⋃ r ∈ BadRanks, {ω | rank ω = r}) := by\n"
            "        apply measure_mono\n"
            "        intro ω hω\n"
            "        exact Set.mem_iUnion.mpr ⟨rank ω, Set.mem_iUnion.mpr ⟨hω, rfl⟩⟩\n"
            "      _ ≤ ∑ r ∈ BadRanks, μ {ω | rank ω = r} := by\n"
            "        exact measure_biUnion_finset_le (μ := μ) BadRanks (fun r => {ω | rank ω = r})\n"
            "      _ ≤ ∑ r ∈ BadRanks, α r := by\n"
            "        exact Finset.sum_le_sum (fun r hr => hRank r hr)\n"
            "      _ ≤ α_total := h_total\n"
            "  have hcoverage : μ ({ω | rank ω ∈ BadRanks}ᶜ) =\n"
            "      1 - μ {ω | rank ω ∈ BadRanks} := by\n"
            "    exact prob_compl_eq_one_sub hBadEvent\n"
            "  rw [hcoverage]\n"
            "  exact tsub_le_tsub_left hbad 1"
        ),
        tags=(
            "certificate_checker",
            "conformal_coverage_certificate",
            "conformal",
            "coverage",
            "rank",
            "finite_sample",
            "kernel_smoke",
        ),
        expected_lemmas=(
            "measure_mono",
            "measure_biUnion_finset_le",
            "Finset.sum_le_sum",
            "prob_compl_eq_one_sub",
            "tsub_le_tsub_left",
        ),
        depends_on=("finite_conformal_rank_coverage_counting",),
    ),
}


def all_certificate_checker_obligations() -> list[FormalObligation]:
    return list(CERTIFICATE_CHECKER_OBLIGATIONS.values())


def get_certificate_checker_obligation(obligation_id: str) -> FormalObligation:
    try:
        return CERTIFICATE_CHECKER_OBLIGATIONS[obligation_id]
    except KeyError as exc:
        known = ", ".join(sorted(CERTIFICATE_CHECKER_OBLIGATIONS))
        raise KeyError(f"unknown certificate checker obligation {obligation_id!r}; known: {known}") from exc


async def audit_stat_claim_certificate_checkers(
    verifier: ProofVerifier,
    out_dir: Path,
    *,
    ids: list[str] | None = None,
    export_lean: bool = True,
) -> dict[str, object]:
    """Verify small statistical certificate-checker soundness theorems.

    These checks are proof evidence only for the encoded checker theorem when
    `kernel_verified=true`. They do not verify the source paper theorem, the
    discovery step, or semantic faithfulness of any extracted statement.
    """

    obligations = (
        [get_certificate_checker_obligation(obligation_id) for obligation_id in ids]
        if ids
        else all_certificate_checker_obligations()
    )
    retriever = ProofBankRetriever()
    out_dir.mkdir(parents=True, exist_ok=True)
    lean_dir = out_dir / "lean"
    if export_lean:
        lean_dir.mkdir(parents=True, exist_ok=True)

    checks: list[ProofCheck] = []
    attempt_records = []
    for attempt_index, obligation in enumerate(obligations, start=1):
        hits = retriever.retrieve(query_for_obligation(obligation), candidates=obligations, k=5)
        check = await verifier.verify(obligation, obligation.proof_body, hits)
        checks.append(check)
        attempt_records.append(
            build_proof_attempt_record(
                obligation,
                check,
                attempt_index=attempt_index,
            )
        )
        if export_lean:
            (lean_dir / f"{obligation.id}.lean").write_text(
                splice_proof(obligation.formal_statement, obligation.proof_body),
                encoding="utf-8",
            )

    attempt_log_manifest = write_proof_attempt_log(attempt_records, out_dir)
    n_verified = sum(1 for check in checks if check.ok)
    n_kernel = sum(1 for check in checks if check.kernel_verified)
    payload = {
        "schema_version": STAT_CLAIM_CERTIFICATE_CHECKER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verifier": getattr(verifier, "name", type(verifier).__name__),
        "verification_strength": _verification_strength(checks),
        "n_obligations": len(obligations),
        "n_verified": n_verified,
        "n_kernel_verified": n_kernel,
        "n_non_kernel_verified": sum(1 for check in checks if check.ok and not check.kernel_verified),
        "all_verified": n_verified == len(checks),
        "all_kernel_verified": bool(checks) and all(check.kernel_verified for check in checks),
        "proof_evidence_status": (
            KERNEL_VERIFIED_STATUS
            if bool(checks) and all(check.kernel_verified for check in checks)
            else NOT_KERNEL_VERIFIED_STATUS
        ),
        "obligation_fingerprint": stable_hash([asdict(obligation) for obligation in obligations]),
        "checks": [asdict(check) for check in checks],
        "lean_export_dir": str(lean_dir) if export_lean else "",
        "proof_attempt_log": attempt_log_manifest,
        "all_ok": n_verified == len(checks),
        "limitations": [
            "Kernel verification of this checker proves only the encoded certificate theorem.",
            "A worker-generated witness still needs checker validation and claim-ledger linkage.",
            "The source paper theorem remains unproved unless the extracted statement, assumptions, and final theorem are separately verified.",
        ],
    }
    (out_dir / "stat_claim_certificate_checker_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "stat_claim_certificate_checker_audit.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )
    return payload


def _verification_strength(checks: list[ProofCheck]) -> str:
    strengths = sorted({check.verification_strength for check in checks if check.verification_strength})
    if not strengths:
        return "unknown"
    if len(strengths) == 1:
        return strengths[0]
    return "mixed:" + ",".join(strengths)


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Statistical Claim Certificate Checker Audit",
        "",
        f"- Verifier: `{payload.get('verifier')}`",
        f"- Verified: `{payload.get('n_verified')}/{payload.get('n_obligations')}`",
        f"- Kernel verified: `{payload.get('n_kernel_verified')}/{payload.get('n_obligations')}`",
        f"- Proof status: `{payload.get('proof_evidence_status')}`",
        "",
        "## Honesty Boundary",
        "",
    ]
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
