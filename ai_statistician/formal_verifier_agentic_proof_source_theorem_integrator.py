from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash
from .formal_verifier_agentic_proof_execution_artifact_verifier import (
    FORBIDDEN_ARTIFACT_TOKENS,
    _lean_command,
    _run_local_lean,
)


FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_INTEGRATOR_SCHEMA_VERSION = 1
PROOF_EVIDENCE_STATUS = "SOURCE_THEOREM_INTEGRATOR_NOT_PROOF_EVIDENCE"
PROOF_EVIDENCE_BOUNDARY = (
    "Source-theorem integration rows are proof evidence only when the exact "
    "source theorem declaration, not a route probe, passes local Lean/AXLE "
    "with source_theorem_kernel_verified=true."
)
ROUTE_PROBE_MARKERS = (
    "route probe",
    "route-probe",
    "_route_probe",
    "not theorem proof evidence",
    "not source theorem proof",
)


@dataclass(frozen=True)
class FormalVerifierAgenticProofSourceTheoremIntegratorRow:
    schema_version: int
    source_theorem_integration_id: str
    source_theorem_promotion_id: str
    promotion_status: str
    target_theorem_name: str
    target_prover_family: str
    formal_statement_sketch: str
    formal_imports: tuple[str, ...]
    exact_source_candidate_path: str
    candidate_artifact_path: str
    artifact_kernel_verified: bool
    source_theorem_target_known: bool
    source_theorem_target_provenance: dict[str, object]
    exact_declaration_present: bool
    vacuous_true_target_detected: bool
    route_probe_detected: bool
    target_assumption_detected: bool
    local_lean_requested: bool
    local_lean_checked: bool
    local_lean_compiled: bool
    source_theorem_kernel_verified: bool
    verifier: str
    verification_strength: str
    lean_command: tuple[str, ...]
    lean_project: str
    lean_timeout: int
    returncode: int
    diagnostics: tuple[str, ...]
    forbidden_tokens_found: tuple[str, ...]
    integration_status: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_agentic_proof_source_theorem_integrator(
    formal_verifier_agentic_proof_source_theorem_promotion_queue_dir: Path,
    out_dir: Path | None = None,
    *,
    lean_project: str | Path | None = None,
    lean_timeout: int = 90,
    lean_command: tuple[str, ...] | None = None,
    local_lean: bool = True,
) -> dict[str, object]:
    """Attempt exact source-theorem integration from promotion queue rows."""

    errors: list[str] = []
    queue_manifest_path = (
        formal_verifier_agentic_proof_source_theorem_promotion_queue_dir
        / "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest.json"
    )
    queue_payload = _read_json(queue_manifest_path, errors)
    project_path = Path(lean_project) if lean_project else None
    command = lean_command or _lean_command(project_path)
    rows = [
        _integrator_row(
            row,
            local_lean=local_lean,
            lean_project=project_path,
            lean_timeout=lean_timeout,
            lean_command=command,
        )
        for row in queue_payload.get("rows", [])
        if isinstance(row, dict)
    ]
    by_status = Counter(row.integration_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_INTEGRATOR_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_agentic_proof_source_theorem_promotion_queue_dir": str(
            formal_verifier_agentic_proof_source_theorem_promotion_queue_dir
        ),
        "formal_verifier_agentic_proof_source_theorem_promotion_queue_manifest": str(
            queue_manifest_path
        ),
        "local_lean_requested": local_lean,
        "lean_project": str(project_path or ""),
        "lean_timeout": lean_timeout,
        "lean_command": list(command),
        "n_promotion_rows": len(queue_payload.get("rows", []) or []),
        "n_integration_rows": len(rows),
        "n_exact_declaration_present": sum(
            1 for row in rows if row.exact_declaration_present
        ),
        "n_vacuous_true_target_detected": sum(
            1 for row in rows if row.vacuous_true_target_detected
        ),
        "n_route_probe_detected": sum(1 for row in rows if row.route_probe_detected),
        "n_target_assumption_detected": sum(
            1 for row in rows if row.target_assumption_detected
        ),
        "n_local_lean_checked": sum(1 for row in rows if row.local_lean_checked),
        "n_local_lean_compiled": sum(1 for row in rows if row.local_lean_compiled),
        "n_source_theorem_kernel_verified": sum(
            1 for row in rows if row.source_theorem_kernel_verified
        ),
        "n_unsupported_target_prover_rows": by_status.get(
            "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_INTEGRATOR",
            0,
        ),
        "by_target_prover_family": dict(
            sorted(Counter(row.target_prover_family for row in rows).items())
        ),
        "n_ready_for_local_lean": by_status.get(
            "EXACT_SOURCE_THEOREM_READY_FOR_LOCAL_LEAN",
            0,
        ),
        "n_blocked_route_probe": by_status.get("BLOCKED_ROUTE_PROBE_ARTIFACT", 0),
        "n_blocked_vacuous_true_target": by_status.get(
            "BLOCKED_VACUOUS_TRUE_SOURCE_THEOREM",
            0,
        ),
        "n_ok": sum(1 for row in rows if row.ok),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "by_integration_status": dict(sorted(by_status.items())),
        "rows": [asdict(row) for row in rows],
        "source_theorem_integrator_fingerprint": stable_hash(
            [asdict(row) for row in rows]
        ),
        "proof_evidence_status": (
            "SOURCE_THEOREM_INTEGRATOR_HAS_KERNEL_EVIDENCE"
            if any(row.source_theorem_kernel_verified for row in rows)
            else PROOF_EVIDENCE_STATUS
        ),
        "proof_evidence_boundary": PROOF_EVIDENCE_BOUNDARY,
        "limitations": [
            "route probes are rejected as source theorem proofs",
            "artifact_kernel_verified is insufficient for source theorem promotion",
            "non-Lean target-prover rows are explicit skips for this Lean source-theorem integrator",
            "exact source theorem proof requires the target declaration itself to pass Lean/AXLE",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_agentic_proof_source_theorem_integrator_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir / "formal_verifier_agentic_proof_source_theorem_integrator.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir / "formal_verifier_agentic_proof_source_theorem_integrator.md"
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


def _integrator_row(
    row: dict[str, Any],
    *,
    local_lean: bool,
    lean_project: Path | None,
    lean_timeout: int,
    lean_command: tuple[str, ...],
) -> FormalVerifierAgenticProofSourceTheoremIntegratorRow:
    errors: list[str] = []
    promotion_status = str(row.get("promotion_status", "") or "")
    promotion_id = str(row.get("source_theorem_promotion_id", "") or "")
    target_theorem_name = str(row.get("target_theorem_name", "") or "").strip()
    target_prover_family = _target_prover_family(row)
    formal_statement_sketch = _formal_statement_sketch(row)
    formal_imports = _formal_imports(row)
    candidate_artifact_path = str(row.get("candidate_artifact_path", "") or "")
    exact_source_candidate_path = str(
        row.get("source_theorem_candidate_path")
        or row.get("source_theorem_artifact_path")
        or candidate_artifact_path
    )
    source_path = Path(exact_source_candidate_path)
    artifact_kernel_verified = bool(row.get("artifact_kernel_verified", False))
    source_theorem_target_known = bool(row.get("source_theorem_target_known", False))
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
    if promotion_id:
        source_theorem_target_provenance.setdefault(
            "source_theorem_promotion_id",
            promotion_id,
        )
    if target_theorem_name:
        source_theorem_target_provenance.setdefault(
            "target_lean_declaration",
            target_theorem_name,
        )
    source = ""
    unsupported_target_prover = (
        promotion_status
        == "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_PROMOTION_QUEUE"
        or not _is_lean_target(row)
    )
    if unsupported_target_prover:
        pass
    elif promotion_status != "READY_FOR_SOURCE_THEOREM_INTEGRATION":
        errors.append("promotion row is not ready for source theorem integration")
    if not unsupported_target_prover and not target_theorem_name:
        errors.append("target_theorem_name missing")
    if unsupported_target_prover:
        pass
    elif not exact_source_candidate_path:
        errors.append("exact source candidate path missing")
    elif not source_path.exists():
        errors.append(f"exact source candidate missing: {source_path}")
    else:
        try:
            source = source_path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"failed to read exact source candidate: {type(exc).__name__}: {exc}")
    lower_source = source.lower()
    forbidden_tokens_found = tuple(
        token for token in FORBIDDEN_ARTIFACT_TOKENS if token in source
    )
    exact_declaration_present = bool(
        target_theorem_name and _has_exact_declaration(source, target_theorem_name)
    )
    vacuous_true_target_detected = bool(
        target_theorem_name and _has_vacuous_true_target(source, target_theorem_name)
    )
    route_probe_detected = any(marker in lower_source for marker in ROUTE_PROBE_MARKERS)
    target_assumption_detected = bool(
        target_theorem_name and _has_target_as_true_assumption(source, target_theorem_name)
    )
    if forbidden_tokens_found:
        errors.append(
            "exact source candidate contains forbidden tokens: "
            + ", ".join(forbidden_tokens_found)
        )
    if source and not exact_declaration_present:
        errors.append("exact target declaration is missing")
    if vacuous_true_target_detected:
        errors.append("candidate source theorem target has vacuous True conclusion")
    if route_probe_detected:
        errors.append("candidate is a route probe, not the exact source theorem")
    if target_assumption_detected:
        errors.append("candidate assumes the target theorem as a True hypothesis")

    checked = False
    compiled = False
    returncode = -1
    diagnostics: tuple[str, ...] = ()
    verifier = "local.lean_source_theorem_integrator"
    verification_strength = "source_theorem_integration_static"
    if unsupported_target_prover:
        integration_status = "UNSUPPORTED_TARGET_PROVER_FOR_SOURCE_THEOREM_INTEGRATOR"
    elif promotion_status != "READY_FOR_SOURCE_THEOREM_INTEGRATION":
        integration_status = "SKIPPED_PROMOTION_STATUS"
    elif route_probe_detected:
        integration_status = "BLOCKED_ROUTE_PROBE_ARTIFACT"
    elif vacuous_true_target_detected:
        integration_status = "BLOCKED_VACUOUS_TRUE_SOURCE_THEOREM"
    elif target_assumption_detected:
        integration_status = "BLOCKED_TARGET_ASSUMED_AS_HYPOTHESIS"
    elif errors:
        integration_status = "BLOCKED_EXACT_SOURCE_THEOREM_STATIC_CHECK"
    elif not local_lean:
        integration_status = "EXACT_SOURCE_THEOREM_READY_FOR_LOCAL_LEAN"
    elif not lean_command:
        diagnostics = ("lean executable not found",)
        errors.append("lean executable not found")
        integration_status = "LOCAL_LEAN_UNAVAILABLE"
    else:
        checked = True
        compiled, returncode, diagnostics = _run_local_lean(
            source_path,
            lean_command=lean_command,
            lean_project=lean_project,
            timeout_s=lean_timeout,
        )
        verification_strength = "local_lean_exact_source_theorem_kernel"
        integration_status = (
            "SOURCE_THEOREM_KERNEL_VERIFIED"
            if compiled
            else "SOURCE_THEOREM_LOCAL_LEAN_FAILED"
        )
        if not compiled:
            errors.append("local Lean exact source theorem check failed")
    source_theorem_kernel_verified = (
        integration_status == "SOURCE_THEOREM_KERNEL_VERIFIED"
    )
    integration_id = (
        "formal_verifier_agentic_proof_source_theorem_integrator:"
        + stable_hash(
            [promotion_id, target_theorem_name, exact_source_candidate_path, lean_command]
        )[:16]
    )
    return FormalVerifierAgenticProofSourceTheoremIntegratorRow(
        schema_version=FORMAL_VERIFIER_AGENTIC_PROOF_SOURCE_THEOREM_INTEGRATOR_SCHEMA_VERSION,
        source_theorem_integration_id=integration_id,
        source_theorem_promotion_id=promotion_id,
        promotion_status=promotion_status,
        target_theorem_name=target_theorem_name,
        target_prover_family=target_prover_family,
        formal_statement_sketch=formal_statement_sketch,
        formal_imports=formal_imports,
        exact_source_candidate_path=exact_source_candidate_path,
        candidate_artifact_path=candidate_artifact_path,
        artifact_kernel_verified=artifact_kernel_verified,
        source_theorem_target_known=source_theorem_target_known,
        source_theorem_target_provenance=source_theorem_target_provenance,
        exact_declaration_present=exact_declaration_present,
        vacuous_true_target_detected=vacuous_true_target_detected,
        route_probe_detected=route_probe_detected,
        target_assumption_detected=target_assumption_detected,
        local_lean_requested=local_lean,
        local_lean_checked=checked,
        local_lean_compiled=compiled,
        source_theorem_kernel_verified=source_theorem_kernel_verified,
        verifier=verifier,
        verification_strength=verification_strength,
        lean_command=lean_command,
        lean_project=str(lean_project or ""),
        lean_timeout=lean_timeout,
        returncode=returncode,
        diagnostics=diagnostics,
        forbidden_tokens_found=forbidden_tokens_found,
        integration_status=integration_status,
        proof_evidence_status=(
            "SOURCE_THEOREM_KERNEL_PROOF_EVIDENCE"
            if source_theorem_kernel_verified
            else PROOF_EVIDENCE_STATUS
        ),
        proof_evidence_boundary=PROOF_EVIDENCE_BOUNDARY,
        ok=not errors,
        errors=tuple(errors),
    )


def _has_exact_declaration(source: str, declaration_name: str) -> bool:
    if not source or not declaration_name:
        return False
    pattern = r"\b(?:theorem|lemma)\s+" + re.escape(declaration_name) + r"\b"
    return re.search(pattern, source) is not None


def _has_vacuous_true_target(source: str, declaration_name: str) -> bool:
    if not source or not declaration_name:
        return False
    pattern = (
        r"\b(?:theorem|lemma)\s+"
        + re.escape(declaration_name)
        + r"\b(?:(?!:=).)*:\s*True\s*:="
    )
    return re.search(pattern, source, flags=re.DOTALL) is not None


def _has_target_as_true_assumption(source: str, declaration_name: str) -> bool:
    if not source or not declaration_name:
        return False
    pattern = r"\(\s*" + re.escape(declaration_name) + r"\s*:\s*True\s*\)"
    return re.search(pattern, source) is not None


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


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Agentic Proof Source-Theorem Integrator",
        "",
        f"- Rows: {payload.get('n_ok')}/{payload.get('n_integration_rows')}",
        f"- Exact declarations: {payload.get('n_exact_declaration_present')}",
        f"- Vacuous True targets blocked: {payload.get('n_blocked_vacuous_true_target')}",
        f"- Route probes blocked: {payload.get('n_blocked_route_probe')}",
        f"- Unsupported target-prover rows: {payload.get('n_unsupported_target_prover_rows')}",
        f"- Target prover families: {payload.get('by_target_prover_family')}",
        f"- Source theorem kernel verified: {payload.get('n_source_theorem_kernel_verified')}",
        f"- Lean command: `{payload.get('lean_command')}`",
        f"- Fingerprint: `{payload.get('source_theorem_integrator_fingerprint')}`",
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
            f"- `{row.get('target_theorem_name')}`: "
            f"{row.get('integration_status')} "
            f"target={row.get('target_prover_family')} "
            f"source_kernel={row.get('source_theorem_kernel_verified')}"
        )
        lines.append(f"  candidate: `{row.get('exact_source_candidate_path')}`")
        lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    return "\n".join(lines) + "\n"
