from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_OBLIGATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FormalVerifierReplayRepairPatchRerunResidualObligationRow:
    schema_version: int
    residual_obligation_id: str
    rerun_calibration_id: str
    rerun_id: str
    rerun_attempt_id: str
    replay_id: str
    route_id: str
    display_name: str
    target_theorem_name: str
    candidate_bridge_lemma_name: str
    patched_artifact_path: str
    patch_rerun_calibration_status: str
    residual_gap: str
    residual_kind: str
    source_support_classification: str
    action_class: str
    action_type: str
    proof_bank_action_id: str
    priority: str
    priority_rank: int
    exact_proof_bank_obligation: str
    proof_bank_bridge_obligations: tuple[str, ...]
    local_candidate_declarations: tuple[str, ...]
    external_candidate_declarations: tuple[str, ...]
    expected_premises: tuple[str, ...]
    required_gate: str
    next_action: str
    proof_evidence_status: str
    proof_evidence_boundary: str
    ok: bool
    errors: tuple[str, ...] = ()


def export_formal_verifier_replay_repair_patch_rerun_residual_obligations(
    formal_verifier_replay_repair_patch_rerun_calibration_dir: Path,
    primitive_source_coverage_dir: Path,
    proof_bank_actions_dir: Path,
    out_dir: Path | None = None,
) -> dict[str, object]:
    """Export proof/library work items still blocking calibrated patch reruns."""

    errors: list[str] = []
    calibration_manifest_path = (
        formal_verifier_replay_repair_patch_rerun_calibration_dir
        / "formal_verifier_replay_repair_patch_rerun_calibration_manifest.json"
    )
    coverage_manifest_path = (
        primitive_source_coverage_dir / "primitive_source_coverage_manifest.json"
    )
    proof_bank_action_manifest_path = proof_bank_actions_dir / "proof_bank_action_manifest.json"
    calibration_payload = _read_json(calibration_manifest_path, errors)
    coverage_payload = _read_json(coverage_manifest_path, errors)
    action_payload = _read_json(proof_bank_action_manifest_path, errors)
    calibration_rows = [
        row for row in calibration_payload.get("rows", []) if isinstance(row, dict)
    ]
    coverage_by_primitive = {
        str(row.get("primitive", "")): row
        for row in coverage_payload.get("rows", [])
        if isinstance(row, dict) and str(row.get("primitive", ""))
    }
    actions_by_primitive = {
        str(row.get("primitive", "")): row
        for row in action_payload.get("actions", [])
        if isinstance(row, dict) and str(row.get("primitive", ""))
    }
    rows: list[FormalVerifierReplayRepairPatchRerunResidualObligationRow] = []
    for calibration_row in calibration_rows:
        if str(calibration_row.get("patch_rerun_calibration_status", "")) == (
            "full_route_kernel_verified"
        ):
            continue
        for residual_kind, residual_gap in _residual_work_items(calibration_row):
            rows.append(
                _residual_row(
                    calibration_row,
                    residual_kind=residual_kind,
                    residual_gap=residual_gap,
                    coverage_row=coverage_by_primitive.get(residual_gap, {}),
                    action_row=actions_by_primitive.get(residual_gap, {}),
                )
            )
    by_action_class = Counter(row.action_class for row in rows)
    by_support = Counter(row.source_support_classification for row in rows)
    by_priority = Counter(row.priority for row in rows)
    by_status = Counter(row.patch_rerun_calibration_status for row in rows)
    payload: dict[str, object] = {
        "schema_version": (
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_OBLIGATION_SCHEMA_VERSION
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "formal_verifier_replay_repair_patch_rerun_calibration_dir": str(
            formal_verifier_replay_repair_patch_rerun_calibration_dir
        ),
        "formal_verifier_replay_repair_patch_rerun_calibration_manifest": str(
            calibration_manifest_path
        ),
        "primitive_source_coverage_dir": str(primitive_source_coverage_dir),
        "primitive_source_coverage_manifest": str(coverage_manifest_path),
        "proof_bank_actions_dir": str(proof_bank_actions_dir),
        "proof_bank_action_manifest": str(proof_bank_action_manifest_path),
        "n_source_calibration_rows": len(calibration_rows),
        "n_unverified_calibration_rows": sum(
            1
            for row in calibration_rows
            if str(row.get("patch_rerun_calibration_status", ""))
            != "full_route_kernel_verified"
        ),
        "n_residual_obligation_rows": len(rows),
        "n_ok": sum(1 for row in rows if row.ok),
        "n_routes_with_residual_obligations": len({row.rerun_id for row in rows}),
        "n_unique_residual_gaps": len({row.residual_gap for row in rows}),
        "n_exact_proof_bank_reuse": by_action_class.get(
            "reuse_exact_proof_bank_obligation",
            0,
        ),
        "n_compose_existing_bridge_chain": by_action_class.get(
            "compose_existing_bridge_chain",
            0,
        ),
        "n_add_minimal_wrapper": by_action_class.get("add_minimal_wrapper", 0),
        "n_design_bridge_lemma": by_action_class.get("design_bridge_lemma", 0),
        "n_source_discovery_needed": by_action_class.get("source_discovery_needed", 0),
        "by_action_class": dict(sorted(by_action_class.items())),
        "by_source_support_classification": dict(sorted(by_support.items())),
        "by_priority": dict(sorted(by_priority.items())),
        "by_patch_rerun_calibration_status": dict(sorted(by_status.items())),
        "all_ok": not errors and all(row.ok for row in rows),
        "errors": errors,
        "rows": [asdict(row) for row in rows],
        "residual_obligation_fingerprint": stable_hash([asdict(row) for row in rows]),
        "limitations": [
            "residual obligation rows are proof/library work contracts, not proof evidence",
            "exact proof-bank matches still need theorem composition into the route before promotion",
            "proof evidence starts only after the patched rerun recalibrates as full_route_kernel_verified",
        ],
    }
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_obligations_manifest.json"
        ).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_obligations.jsonl"
        ).write_text(
            "\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows)
            + ("\n" if rows else ""),
            encoding="utf-8",
        )
        (
            out_dir
            / "formal_verifier_replay_repair_patch_rerun_residual_obligations.md"
        ).write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def _residual_work_items(row: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    residual_gaps = _str_tuple(row.get("residual_formal_gaps", []))
    if residual_gaps:
        return tuple(("residual_formal_gap", gap) for gap in residual_gaps)
    bridge = str(row.get("candidate_bridge_lemma_name", ""))
    if bool(row.get("contains_patch_proposal_marker", False)) and bridge:
        return (("candidate_bridge_proof", bridge),)
    return ()


def _residual_row(
    calibration_row: dict[str, Any],
    *,
    residual_kind: str,
    residual_gap: str,
    coverage_row: dict[str, Any],
    action_row: dict[str, Any],
) -> FormalVerifierReplayRepairPatchRerunResidualObligationRow:
    errors: list[str] = []
    rerun_calibration_id = str(calibration_row.get("rerun_calibration_id", ""))
    rerun_id = str(calibration_row.get("rerun_id", ""))
    replay_id = str(calibration_row.get("replay_id", ""))
    route_id = str(calibration_row.get("route_id", ""))
    display_name = str(calibration_row.get("display_name", ""))
    action_class = str(
        action_row.get(
            "action_class",
            coverage_row.get("action_class", "source_discovery_needed"),
        )
    )
    support_classification = str(
        coverage_row.get("classification", "coverage_missing_for_residual_gap")
    )
    if not rerun_calibration_id:
        errors.append("rerun_calibration_id missing")
    if not rerun_id:
        errors.append("rerun_id missing")
    if not replay_id:
        errors.append("replay_id missing")
    if not route_id:
        errors.append("route_id missing")
    if not display_name:
        errors.append("display_name missing")
    if not residual_gap:
        errors.append("residual_gap missing")
    if action_class not in {
        "reuse_exact_proof_bank_obligation",
        "compose_existing_bridge_chain",
        "add_minimal_wrapper",
        "design_bridge_lemma",
        "formalize_assumption_interface",
        "design_from_first_principles",
        "port_external_source",
        "source_discovery_needed",
    }:
        errors.append(f"unsupported action_class: {action_class}")
    priority = str(action_row.get("priority", _priority_for_action_class(action_class)))
    return FormalVerifierReplayRepairPatchRerunResidualObligationRow(
        schema_version=(
            FORMAL_VERIFIER_REPLAY_REPAIR_PATCH_RERUN_RESIDUAL_OBLIGATION_SCHEMA_VERSION
        ),
        residual_obligation_id=(
            "formal_verifier_replay_repair_patch_rerun_residual_obligation:"
            f"{stable_hash([rerun_calibration_id, residual_kind, residual_gap])[:16]}"
        ),
        rerun_calibration_id=rerun_calibration_id,
        rerun_id=rerun_id,
        rerun_attempt_id=str(calibration_row.get("rerun_attempt_id", "")),
        replay_id=replay_id,
        route_id=route_id,
        display_name=display_name,
        target_theorem_name=str(calibration_row.get("target_theorem_name", "")),
        candidate_bridge_lemma_name=str(
            calibration_row.get("candidate_bridge_lemma_name", "")
        ),
        patched_artifact_path=str(calibration_row.get("patched_artifact_path", "")),
        patch_rerun_calibration_status=str(
            calibration_row.get("patch_rerun_calibration_status", "")
        ),
        residual_gap=residual_gap,
        residual_kind=residual_kind,
        source_support_classification=support_classification,
        action_class=action_class,
        action_type=str(action_row.get("action_type", _action_type(action_class))),
        proof_bank_action_id=str(action_row.get("action_id", "")),
        priority=priority,
        priority_rank=_priority_rank(priority),
        exact_proof_bank_obligation=str(
            coverage_row.get(
                "exact_proof_bank_obligation",
                action_row.get("primitive", "") if action_class == "reuse_exact_proof_bank_obligation" else "",
            )
        ),
        proof_bank_bridge_obligations=_str_tuple(
            coverage_row.get(
                "proof_bank_bridge_obligations",
                action_row.get("bridge_candidate_obligations", []),
            )
        )[:12],
        local_candidate_declarations=_str_tuple(
            coverage_row.get(
                "local_candidate_declarations",
                action_row.get("candidate_declarations", []),
            )
        )[:8],
        external_candidate_declarations=_str_tuple(
            coverage_row.get("external_candidate_declarations", [])
        )[:8],
        expected_premises=_str_tuple(action_row.get("expected_premises", []))[:16],
        required_gate=str(action_row.get("required_gate", _required_gate(action_class))),
        next_action=_next_action(
            residual_gap=residual_gap,
            action_class=action_class,
            support_classification=support_classification,
            exact_proof_bank_obligation=str(
                coverage_row.get("exact_proof_bank_obligation", "")
            ),
        ),
        proof_evidence_status="RESIDUAL_OBLIGATION_NOT_PROOF_EVIDENCE",
        proof_evidence_boundary=(
            "This residual obligation is a proof/library work contract, not "
            "proof evidence. It is not theorem proof evidence until a "
            "non-placeholder proof or composition passes AXLE/local Lean and "
            "the patched rerun recalibrates as "
            "full_route_kernel_verified."
        ),
        ok=not errors,
        errors=tuple(errors),
    )


def _action_type(action_class: str) -> str:
    return {
        "reuse_exact_proof_bank_obligation": "reuse_verified_proof_bank_obligation",
        "compose_existing_bridge_chain": "compose_verified_bridge_chain_into_frontier_skeleton",
        "add_minimal_wrapper": "add_minimal_verified_wrapper",
        "design_bridge_lemma": "design_missing_bridge_lemma",
        "formalize_assumption_interface": "formalize_assumption_interface",
        "design_from_first_principles": "design_lean_primitive_from_first_principles",
        "port_external_source": "port_external_source_to_local_lean",
        "source_discovery_needed": "expand_source_search_for_residual_gap",
    }.get(action_class, "inspect_residual_gap")


def _required_gate(action_class: str) -> str:
    if action_class == "reuse_exact_proof_bank_obligation":
        return "theorem composition references the verified proof-bank obligation and rerun calibration passes"
    if action_class == "compose_existing_bridge_chain":
        return "non-placeholder bridge-chain composition passes AXLE/local Lean and rerun calibration passes"
    if action_class == "add_minimal_wrapper":
        return "minimal wrapper passes AXLE/local Lean and is reused by the patched route"
    if action_class == "design_bridge_lemma":
        return "new bridge lemma passes AXLE/local Lean and closes the patched rerun residual gap"
    if action_class == "port_external_source":
        return "external source is ported/imported locally and checked by AXLE/local Lean"
    return "source support is found, proved, and rerun calibration reports full_route_kernel_verified"


def _next_action(
    *,
    residual_gap: str,
    action_class: str,
    support_classification: str,
    exact_proof_bank_obligation: str,
) -> str:
    if action_class == "reuse_exact_proof_bank_obligation":
        target = exact_proof_bank_obligation or residual_gap
        return (
            f"compose verified proof-bank obligation `{target}` into the patched "
            "route; do not open a duplicate primitive proof task"
        )
    if action_class == "compose_existing_bridge_chain":
        return f"compose the verified bridge chain for `{residual_gap}` into the route theorem"
    if action_class == "add_minimal_wrapper":
        return f"prove the minimal wrapper needed to expose `{residual_gap}` to the route"
    if action_class == "design_bridge_lemma":
        return f"design and verify a reusable bridge lemma for `{residual_gap}`"
    if action_class == "port_external_source":
        return f"port the external Lean source candidate for `{residual_gap}` and rerun"
    if support_classification == "coverage_missing_for_residual_gap":
        return f"run source coverage expansion for residual gap `{residual_gap}`"
    return f"expand proof search and source retrieval for `{residual_gap}`"


def _priority_for_action_class(action_class: str) -> str:
    if action_class in {"compose_existing_bridge_chain", "add_minimal_wrapper"}:
        return "medium"
    if action_class in {"design_bridge_lemma", "port_external_source", "source_discovery_needed"}:
        return "medium"
    return "low"


def _priority_rank(priority: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(priority, 3)


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


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    if str(value):
        return (str(value),)
    return ()


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Formal Verifier Patch Rerun Residual Obligations",
        "",
        f"- Calibration manifest: `{payload.get('formal_verifier_replay_repair_patch_rerun_calibration_manifest')}`",
        f"- Residual obligations: {payload.get('n_ok')}/{payload.get('n_residual_obligation_rows')} audit-clean",
        f"- Routes with residual obligations: {payload.get('n_routes_with_residual_obligations')}",
        f"- Unique residual gaps: {payload.get('n_unique_residual_gaps')}",
        f"- Exact proof-bank reuse rows: {payload.get('n_exact_proof_bank_reuse')}",
        f"- Bridge-chain rows: {payload.get('n_compose_existing_bridge_chain')}",
        "",
        "These rows are proof/library work contracts, not theorem proof evidence.",
        "",
        "## Top Rows",
        "",
    ]
    rows = payload.get("rows", [])
    if not isinstance(rows, list) or not rows:
        lines.append("No residual proof obligations remain for patch-rerun calibration.")
    else:
        for row in rows[:40]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('display_name')}` -> `{row.get('residual_gap')}` "
                f"({row.get('action_class')}, {row.get('source_support_classification')})"
            )
            lines.append(f"  next: {row.get('next_action')}")
            lines.append(f"  boundary: {row.get('proof_evidence_boundary')}")
    lines.extend(["", "## Honesty Boundary", ""])
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
