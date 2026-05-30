from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .proof_bank import all_obligations, get_obligation, obligations_by_tags, proof_bank_fingerprint
from .proof_attempt_log import build_proof_attempt_record, write_proof_attempt_log
from .retrieval import ProofBankRetriever, query_for_obligation
from .schema import FormalObligation, ProofAttemptRecord, ProofCheck
from .verifier import ProofVerifier, splice_proof


def select_obligations(
    *,
    ids: list[str] | None = None,
    tags: list[str] | None = None,
    require_all_tags: bool = False,
) -> list[FormalObligation]:
    if ids:
        return [get_obligation(obligation_id) for obligation_id in ids]
    if tags:
        return obligations_by_tags(set(tags), require_all=require_all_tags)
    return all_obligations()


async def audit_proof_bank(
    verifier: ProofVerifier,
    out_dir: Path,
    *,
    ids: list[str] | None = None,
    tags: list[str] | None = None,
    require_all_tags: bool = False,
    export_lean: bool = True,
    export_attempt_log: bool = True,
    include_negative_controls: bool = False,
) -> dict[str, object]:
    obligations = select_obligations(ids=ids, tags=tags, require_all_tags=require_all_tags)
    retriever = ProofBankRetriever()
    checks: list[ProofCheck] = []
    attempt_records: list[ProofAttemptRecord] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    lean_dir = out_dir / "lean"
    if export_lean:
        lean_dir.mkdir(parents=True, exist_ok=True)

    obligation_hits = [
        (obligation, retriever.retrieve(query_for_obligation(obligation), k=5))
        for obligation in obligations
    ]
    verify_many = getattr(verifier, "verify_many", None)
    if callable(verify_many):
        positive_checks = await verify_many(
            [
                (obligation, obligation.proof_body, hits)
                for obligation, hits in obligation_hits
            ]
        )
    else:
        positive_checks = [
            await verifier.verify(obligation, obligation.proof_body, hits)
            for obligation, hits in obligation_hits
        ]
    if len(positive_checks) != len(obligation_hits):
        raise RuntimeError(
            f"verifier returned {len(positive_checks)} checks for {len(obligation_hits)} obligations"
        )

    for attempt_index, ((obligation, hits), check) in enumerate(zip(obligation_hits, positive_checks), start=1):
        checks.append(check)
        attempt_records.append(
            build_proof_attempt_record(
                obligation,
                check,
                attempt_index=attempt_index,
            )
        )
        if include_negative_controls:
            negative_check = await verifier.verify(obligation, "", hits)
            attempt_records.append(
                build_proof_attempt_record(
                    obligation,
                    negative_check,
                    attempt_index=attempt_index + len(obligations),
                )
            )
        if export_lean:
            (lean_dir / f"{obligation.id}.lean").write_text(
                splice_proof(obligation.formal_statement, obligation.proof_body),
                encoding="utf-8",
            )

    n_ok = sum(1 for check in checks if check.ok)
    attempt_log_manifest = (
        write_proof_attempt_log(attempt_records, out_dir)
        if export_attempt_log
        else None
    )
    dependency_graph = _audit_dependency_graph(obligations, checks)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verifier": getattr(verifier, "name", type(verifier).__name__),
        "verification_strength": _verification_strength(checks),
        "proof_bank_fingerprint": proof_bank_fingerprint(),
        "n_obligations": len(checks),
        "n_verified": n_ok,
        "n_kernel_verified": sum(1 for check in checks if check.kernel_verified),
        "n_non_kernel_verified": sum(1 for check in checks if check.ok and not check.kernel_verified),
        "all_verified": n_ok == len(checks),
        "all_kernel_verified": bool(checks) and all(check.kernel_verified for check in checks),
        "dependency_graph": dependency_graph,
        "filters": {
            "ids": ids or [],
            "tags": tags or [],
            "require_all_tags": require_all_tags,
        },
        "negative_controls": {
            "enabled": include_negative_controls,
            "candidate": "empty proof body",
            "n_expected": len(obligations) if include_negative_controls else 0,
            "n_recorded": (
                sum(1 for row in attempt_records if not row.ok)
                if include_negative_controls
                else 0
            ),
        },
        "checks": [asdict(check) for check in checks],
        "lean_export_dir": str(lean_dir) if export_lean else None,
        "proof_attempt_log": attempt_log_manifest,
    }
    (out_dir / "proof_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
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


def _audit_dependency_graph(
    obligations: list[FormalObligation],
    checks: list[ProofCheck],
) -> dict[str, object]:
    bank_ids = {obligation.id for obligation in all_obligations()}
    selected_ids = {obligation.id for obligation in obligations}
    verified_ids = {check.obligation_id for check in checks if check.ok}
    rows: list[dict[str, object]] = []
    for obligation in obligations:
        missing_from_bank = [dep for dep in obligation.depends_on if dep not in bank_ids]
        selected_unverified = [
            dep for dep in obligation.depends_on if dep in selected_ids and dep not in verified_ids
        ]
        rows.append(
            {
                "obligation_id": obligation.id,
                "depends_on": list(obligation.depends_on),
                "n_dependencies": len(obligation.depends_on),
                "missing_from_bank": missing_from_bank,
                "selected_unverified": selected_unverified,
                "ok": not missing_from_bank and not selected_unverified,
            }
        )
    n_edges = sum(int(row["n_dependencies"]) for row in rows)
    n_with_dependencies = sum(1 for row in rows if row["depends_on"])
    return {
        "n_edges": n_edges,
        "n_with_dependencies": n_with_dependencies,
        "all_known": all(not row["missing_from_bank"] for row in rows),
        "selected_dependencies_verified": all(not row["selected_unverified"] for row in rows),
        "all_ok": all(bool(row["ok"]) for row in rows),
        "rows": rows,
    }
