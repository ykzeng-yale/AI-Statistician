from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_PROMOTION_QUEUE_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "SOURCE_THEOREM_PROMOTION_QUEUE_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Agentic source-theorem promotion queue rows are operational work orders. "
    "An artifact-kernel-verified route probe is not source theorem proof "
    "evidence until the source theorem or residual gap itself passes AXLE/local "
    "Lean without placeholders."
)


@dataclass(frozen=True)
class FormalVerifierAgenticProofSourceTheoremPromotionQueueRow:
    schema_version: int
    source_theorem_promotion_id: str
    artifact_verification_id: str
    materialization_id: str
    execution_queue_id: str
    display_name: str
    target_theorem_name: str
    target_prover_family: str
    formal_statement_sketch: str
    formal_imports: tuple[str, ...]
    candidate_artifact_path: str
    target_lean_declaration: str
    target_lean_line: int
    artifact_kernel_verified: bool
    source_theorem_kernel_verified: bool
    source_theorem_target_known: bool
    source_theorem_target_provenance: dict[str, object]
    verifier: str
    verification_strength: str
    source_verification_status: str
    promotion_status: str
    owner_agent: str
    action_type: str
    priority: str
    required_gate: str
    required_inputs: tuple[str, ...]
    command_plan: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_source_theorem_promotion_queue(
    formal_verifier_agentic_proof_execution_artifact_verifier_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Queue source-theorem integration tasks from verified agentic artifacts."""

    errors: list[str] = []
    verifier_manifest_path = (
        formal_verifier_agentic_proof_execution_artifact_verifier_dir
        / "formal_verifier_agentic_proof_execution_artifact_verifier_manifest.json"
    )
    verifier_payload = _read_json(verifier_manifest_path, errors)
    verifier_rows = [
        row for row in verifier_payload.get("rows", []) if isinstance(row, dict)
    ]
    rows = [_promotion_row(row) for row in verifier_rows]
    by_status = Counter(row.promotion_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_PROMOTION_QUEUE_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_execution_artifact_verifier_dir": str(
            formal_verifier_agentic_proof_execution_artifact_verifier_dir
        ),
        "formal_verifier_agentic_proof_execution_artifact_verifier_manifest": str(
            verifier_manifest_path
        ),
        "n_artifact_verifier_rows": len(verifier_rows),
        "n_promotion_rows": len(rows),
        "n_artifact_kernel_verified_inputs": sum(
            1 for row in rows if row.artifact_kernel_verified
        ),
        "n_source_theorem_kernel_verified": sum(
            1 for row in rows if row.source_theorem_kernel_verified
        ),
        "n_ready_for_source_theorem_integration": by_status.get(
            "READY_FOR_SOURCE_THEOREM_INTEGRATION",
            0,
        ),
        "n_needs_source_theorem_target_resolution": by_status.get(
            "NEEDS_SOURCE_THEOREM_TARGET_RESOLUTION",
            0,
        ),
        "n_blocked_artifact_verification_failed": by_status.get(
            "BLOCKED_ARTIFACT_VERIFICATION_FAILED",
            0,
        ),
        "n_unsupported_target_prover_rows": by_status.get(
            "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_PROMOTION_QUEUE",
            0,
        ),
        "by_target_prover_family": dict(
            sorted(Counter(row.target_prover_family for row in rows).items())
        ),
        "n_source_theorem_target_known": sum(
            1 for row in rows if row.source_theorem_target_known
        ),
        "n_needs_source_theorem_target": sum(
            1 for row in rows if not row.source_theorem_target_known
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_promotion_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "source_theorem_promotion_queue_fingerprint": stable_hash(
            [asdict(row) for row in rows]
        ),
        "proof_evidence_status": PROOF_EVIDENCE_STATUS,
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "route-probe artifact verification is not source theorem verification",
            "source theorem targets may need to be resolved from the route ledger",
            "non-Lean target-prover rows are explicit skips for this Lean source-theorem promotion queue",
            "promotion requires full-route Lean/AXLE evidence before claim-ledger updates",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formal_verifier_agentic_proof_source_theorem_promotion_queue.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formal_verifier_agentic_proof_source_theorem_promotion_queue.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _target_prover_family(row: dict[str, Any]) -> str:
    provenance = row.get("source_theorem_target_provenance", {})
    if not isinstance(provenance, dict):
        provenance = {}
    return str(
        row.get("target_prover_family")
        or provenance.get("target_prover_family")
        or "lean4"
    ).strip()


def _is_lean_target(row: dict[str, Any]) -> bool:
    return _target_prover_family(row).lower() in {"lean", "lean4"}


def _formal_statement_sketch(row: dict[str, Any]) -> str:
    provenance = row.get("source_theorem_target_provenance", {})
    if not isinstance(provenance, dict):
        provenance = {}
    return str(
        row.get("formal_statement_sketch")
        or provenance.get("formal_statement_sketch")
        or row.get("lean_statement_sketch")
        or ""
    ).strip()


def _formal_imports(row: dict[str, Any]) -> tuple[str, ...]:
    provenance = row.get("source_theorem_target_provenance", {})
    if not isinstance(provenance, dict):
        provenance = {}
    values = row.get("formal_imports") or provenance.get("formal_imports") or []
    if isinstance(values, (str, bytes)):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return ()
    return tuple(str(item) for item in values if str(item))


def _promotion_row(
    row: dict[str, Any],
) -> FormalVerifierAgenticProofSourceTheoremPromotionQueueRow:
    errors: list[str] = []
    artifact_verification_id = str(row.get("artifact_verification_id", ""))
    materialization_id = str(row.get("materialization_id", ""))
    execution_queue_id = str(row.get("execution_queue_id", ""))
    display_name = str(row.get("display_name", ""))
    target_theorem_name = str(row.get("target_theorem_name", ""))
    target_prover_family = _target_prover_family(row)
    formal_statement_sketch = _formal_statement_sketch(row)
    formal_imports = _formal_imports(row)
    candidate_artifact_path = str(row.get("candidate_artifact_path", ""))
    target_lean_declaration = str(row.get("target_lean_declaration", ""))
    source_verification_status = str(row.get("verification_status", ""))
    artifact_kernel_verified = bool(row.get("artifact_kernel_verified", False))
    source_theorem_kernel_verified = bool(
        row.get("source_theorem_kernel_verified", False)
    )
    source_theorem_target_known = bool(
        row.get("source_theorem_target_known", False)
        or row.get("source_theorem_lean_file", "")
    )
    source_theorem_target_provenance = (
        dict(row.get("source_theorem_target_provenance", {}))
        if isinstance(row.get("source_theorem_target_provenance", {}), dict)
        else {}
    )
    if source_theorem_target_known:
        source_theorem_target_provenance["source_theorem_target_known"] = True
    if target_prover_family:
        source_theorem_target_provenance.setdefault(
            "target_prover_family",
            target_prover_family,
        )
    if formal_statement_sketch:
        source_theorem_target_provenance.setdefault(
            "formal_statement_sketch",
            formal_statement_sketch,
        )
    if formal_imports:
        source_theorem_target_provenance.setdefault(
            "formal_imports",
            list(formal_imports),
        )
    if artifact_verification_id:
        source_theorem_target_provenance.setdefault(
            "artifact_verification_id",
            artifact_verification_id,
        )
    if materialization_id:
        source_theorem_target_provenance.setdefault(
            "materialization_id",
            materialization_id,
        )
    if execution_queue_id:
        source_theorem_target_provenance.setdefault(
            "execution_queue_id",
            execution_queue_id,
        )
    if target_lean_declaration:
        source_theorem_target_provenance.setdefault(
            "target_lean_declaration",
            target_lean_declaration,
        )
    target_lean_line = _int(row.get("target_lean_line"))
    unsupported_target_prover = (
        source_verification_status
        == "UNSUPPORTED_TARGET_PROVER_FOR_LEAN_ARTIFACT_VERIFIER"
        or not _is_lean_target(row)
    )
    if not artifact_verification_id:
        errors.append("artifact_verification_id missing")
    if unsupported_target_prover:
        pass
    elif not candidate_artifact_path:
        errors.append("candidate_artifact_path missing")
    if not unsupported_target_prover and not target_lean_declaration:
        errors.append("target_lean_declaration missing")

    if unsupported_target_prover:
        promotion_status = "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_PROMOTION_QUEUE"
        action_type = "dispatch_source_theorem_to_target_prover_adapter"
        priority = "normal"
        required_gate = (
            "a target-prover-specific materializer, verifier, and source-theorem "
            "promotion adapter handles this formal target before any kernel claim"
        )
        command_plan = (
            "preserve the target-prover-neutral formal statement and imports",
            "route the row to the matching target-prover adapter contract",
            "do not run the Lean source-theorem promotion queue for this row",
        )
    elif source_theorem_kernel_verified:
        promotion_status = "SOURCE_THEOREM_KERNEL_VERIFIED_NO_QUEUE_ACTION"
        action_type = "record_source_theorem_kernel_evidence"
        priority = "high"
        required_gate = (
            "claim ledger and proof bank record source theorem kernel evidence "
            "with verifier manifest attached, then release gates rerun"
        )
        command_plan = (
            "confirm the verifier manifest proves the source theorem, not only the route probe",
            "attach the source theorem verifier manifest to the claim ledger",
            "rerun proof audit and research-system audit release gates",
        )
    elif artifact_kernel_verified and source_theorem_target_known:
        promotion_status = "READY_FOR_SOURCE_THEOREM_INTEGRATION"
        action_type = "integrate_artifact_proof_into_source_theorem"
        priority = "high"
        required_gate = (
            "source theorem or residual gap passes AXLE/local Lean without "
            "sorry/admit/axiom and with statement/header guard preserved"
        )
        command_plan = (
            "resolve the source theorem file and exact statement from the route ledger",
            "reuse the compiled route-probe artifact only as a proof sketch/source",
            "replace the route probe with the real source theorem target under bounded edits",
            "run AXLE or local Lean on the source theorem target",
            "promote only after source_theorem_kernel_verified=true",
        )
    elif artifact_kernel_verified:
        promotion_status = "NEEDS_SOURCE_THEOREM_TARGET_RESOLUTION"
        action_type = "resolve_source_theorem_target_for_artifact"
        priority = "high"
        required_gate = (
            "route ledger resolves the exact source theorem file, declaration, "
            "and statement before integration is attempted"
        )
        command_plan = (
            "resolve the source theorem file and exact statement from the route ledger",
            "attach source_theorem_lean_file or source_theorem_target_known=true to the verifier row",
            "keep the compiled route-probe artifact as artifact-only kernel evidence",
            "rerun source-theorem promotion queue before source integration",
        )
    else:
        promotion_status = "BLOCKED_ARTIFACT_VERIFICATION_FAILED"
        action_type = "repair_generated_artifact_before_source_promotion"
        priority = "high"
        required_gate = (
            "generated artifact compiles under local Lean before source theorem "
            "integration is attempted"
        )
        command_plan = (
            "inspect artifact verifier diagnostics",
            "repair the materialized route-probe artifact inside the bounded block",
            "rerun the artifact verifier",
        )
    required_inputs = (
        (
            "target_prover_family",
            "formal_statement_sketch",
            "formal_imports",
            "target_prover_adapter_contract",
        )
        if unsupported_target_prover
        else (
            "candidate_artifact_path",
            "artifact_verifier_manifest",
            "source_theorem_statement_or_file",
            "full_route_lean_or_axle_verifier_manifest",
        )
    )
    evidence_paths = (
        ()
        if unsupported_target_prover
        else tuple(
            item
            for item in (
                candidate_artifact_path,
                str(row.get("artifact_verifier_manifest", "")),
            )
            if item
        )
    )
    return FormalVerifierAgenticProofSourceTheoremPromotionQueueRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_PROMOTION_QUEUE_SCHEMA_VERSION,
        source_theorem_promotion_id=(
            "formal_verifier_agentic_proof_source_theorem_promotion_queue:"
            + stable_hash(
                [
                    artifact_verification_id,
                    materialization_id,
                    target_theorem_name,
                    source_theorem_target_provenance,
                ]
            )[:16]
        ),
        artifact_verification_id=artifact_verification_id,
        materialization_id=materialization_id,
        execution_queue_id=execution_queue_id,
        display_name=display_name,
        target_theorem_name=target_theorem_name,
        target_prover_family=target_prover_family,
        formal_statement_sketch=formal_statement_sketch,
        formal_imports=formal_imports,
        candidate_artifact_path=candidate_artifact_path,
        target_lean_declaration=target_lean_declaration,
        target_lean_line=target_lean_line,
        artifact_kernel_verified=artifact_kernel_verified,
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        source_theorem_target_known=source_theorem_target_known,
        source_theorem_target_provenance=source_theorem_target_provenance,
        verifier=str(row.get("verifier", "")),
        verification_strength=str(row.get("verification_strength", "")),
        source_verification_status=source_verification_status,
        promotion_status=promotion_status,
        owner_agent="formal_verifier_source_theorem_integrator",
        action_type=action_type,
        priority=priority,
        required_gate=required_gate,
        required_inputs=required_inputs,
        command_plan=command_plan,
        evidence_paths=evidence_paths,
        proof_evidence_status=PROOF_EVIDENCE_STATUS,
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except Exception as exc:
        errors.append(f"failed to parse {path}: {type(exc).__name__}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Agentic Proof Source-Theorem Promotion Queue",
        "",
        f"- Rows: {payload.get('n_ok')}/{payload.get('n_promotion_rows')}",
        f"- Artifact-kernel inputs: {payload.get('n_artifact_kernel_verified_inputs')}",
        f"- Ready for source-theorem integration: {payload.get('n_ready_for_source_theorem_integration')}",
        f"- Unsupported target-prover rows: {payload.get('n_unsupported_target_prover_rows')}",
        f"- Target prover families: {payload.get('by_target_prover_family')}",
        f"- Source theorem kernel verified: {payload.get('n_source_theorem_kernel_verified')}",
        f"- Needs source theorem target: {payload.get('n_needs_source_theorem_target')}",
        f"- Fingerprint: `{payload.get('source_theorem_promotion_queue_fingerprint')}`",
        "",
        str(payload.get("proof_evidence_boundary", "")),
        "",
        "## Rows",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('target_theorem_name')}`: {row.get('promotion_status')} "
            f"target={row.get('target_prover_family')} "
            f"artifact_kernel={row.get('artifact_kernel_verified')} "
            f"source_theorem_kernel={row.get('source_theorem_kernel_verified')}"
        )
        lines.append(f"  action: `{row.get('action_type')}`")
        lines.append(f"  artifact: `{row.get('candidate_artifact_path')}`")
        lines.append(f"  gate: {row.get('required_gate')}")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    return "\n".join(lines) + "\n"
