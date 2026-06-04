from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


LEAN_RAG_PACKAGE_AUDIT_SCHEMA_VERSION = 1
LEAN_RAG_SOURCE_REGISTRY_EXPANSION_SCHEMA_VERSION = 1
LEAN_RAG_SOURCE_EXPANSION_PREFLIGHT_SCHEMA_VERSION = 1
LEAN_RAG_SOURCE_REGISTRY_APPLY_SCHEMA_VERSION = 1
VALID_SOURCE_REGISTRY_SECTIONS = ("local_sources", "external_sources")

REQUIRED_PACKAGE_FILES: tuple[str, ...] = (
    "README.md",
    "docs/OPERATING_GUIDE.md",
    "docs/SCHEMA.md",
    "knowledgebase/source_registry.json",
    "knowledgebase/seed_queries.jsonl",
    "scripts/shared_proof_retrieval.py",
    "scripts/lean_graph_index.py",
    "scripts/external_lean_corpus_index.py",
    "scripts/lean_reuse_corpus_search.py",
    "scripts/refresh_lean_reuse_sources.py",
)

TARGET_LEAN_SOURCE_COVERAGE: tuple[dict[str, object], ...] = (
    {
        "target_id": "mathlib",
        "display_name": "Mathlib",
        "role": "external candidate and documentation source",
        "aliases": ("mathlib4", "mathlib-docs-distribution", "mathlib"),
    },
    {
        "target_id": "statinference_local",
        "display_name": "StatInference local corpus",
        "role": "authoritative local proof corpus",
        "aliases": ("statinference-local", "statinference"),
    },
    {
        "target_id": "empirical_process_lean",
        "display_name": "EmpiricalProcessLEAN package checkout",
        "role": "authoritative empirical-process proof package",
        "aliases": ("empericalprocesslean", "empiricalprocesslean"),
    },
    {
        "target_id": "legacy_ai_statistician_statinference",
        "display_name": "Legacy AI-Statistician StatInference",
        "role": "legacy proof reuse corpus",
        "aliases": (
            "legacy-ai-statistician-statinference",
            "legacy-statinference",
            "ai-statistician-legacy",
        ),
        "registry_candidate_section": "external_sources",
        "registry_candidate": {
            "name": "legacy-ai-statistician-statinference",
            "local_path": "/Users/yukang/AI Statistician/legacy_sources/ai_statistician/StatInference",
            "trust": "candidate search only; local Lean must verify imported uses",
        },
        "source_evidence_urls": (),
        "source_evidence_status": "local path observed in /Users/yukang/AI Statistician/legacy_sources",
    },
    {
        "target_id": "lean_stat_learning_theory",
        "display_name": "lean-stat-learning-theory",
        "role": "statistical learning theorem candidate source",
        "aliases": ("lean-stat-learning-theory", "slt"),
    },
    {
        "target_id": "atlas_lean",
        "display_name": "atlas-lean",
        "role": "broad Lean theorem candidate source",
        "aliases": ("atlas-lean",),
    },
    {
        "target_id": "autoform_bot",
        "display_name": "autoform-bot exports",
        "role": "formalization/automation candidate source",
        "aliases": ("autoform-bot", "facebookresearch-autoform-bot"),
    },
    {
        "target_id": "formal_slt",
        "display_name": "formal_slt",
        "role": "statistical learning theorem candidate source",
        "aliases": ("formal_slt", "formal-slt", "foml", "lean-rademacher"),
        "registry_candidate_section": "external_sources",
        "registry_candidate": {
            "name": "lean-rademacher",
            "url": "https://github.com/auto-res/lean-rademacher",
            "local_path": "/private/tmp/lean-reuse-corpus/lean-rademacher",
            "trust": "candidate search only; local Lean must verify imported uses",
        },
        "source_evidence_urls": (
            "https://github.com/auto-res/lean-rademacher",
            "https://reservoir.lean-lang.org/@auto-res/FoML",
        ),
        "source_evidence_status": "git ls-remote verified https://github.com/auto-res/lean-rademacher",
    },
    {
        "target_id": "lean_rademacher",
        "display_name": "lean_rademacher",
        "role": "Rademacher-complexity candidate source",
        "aliases": ("lean_rademacher", "lean-rademacher"),
        "registry_candidate_section": "external_sources",
        "registry_candidate": {
            "name": "lean-rademacher",
            "url": "https://github.com/auto-res/lean-rademacher",
            "local_path": "/private/tmp/lean-reuse-corpus/lean-rademacher",
            "trust": "candidate search only; local Lean must verify imported uses",
        },
        "source_evidence_urls": (
            "https://github.com/auto-res/lean-rademacher",
            "https://reservoir.lean-lang.org/@auto-res/FoML",
        ),
        "source_evidence_status": "git ls-remote verified https://github.com/auto-res/lean-rademacher",
    },
    {
        "target_id": "lean_machine_learning_lml",
        "display_name": "lean_machine_learning_lml",
        "role": "machine-learning Lean candidate source",
        "aliases": ("lean_machine_learning_lml", "lean-machine-learning-lml", "lml"),
        "registry_candidate_section": "external_sources",
        "registry_candidate": {
            "name": "lean-machine-learning-lml",
            "url": "https://github.com/LeanMachineLearning/LML",
            "local_path": "/private/tmp/lean-reuse-corpus/LML",
            "trust": "candidate search only; local Lean must verify imported uses",
        },
        "source_evidence_urls": ("https://github.com/LeanMachineLearning/LML",),
        "source_evidence_status": "git ls-remote verified https://github.com/LeanMachineLearning/LML",
    },
    {
        "target_id": "brownian_motion_lean",
        "display_name": "brownian_motion_lean",
        "role": "stochastic-process candidate source",
        "aliases": ("brownian_motion_lean", "brownian-motion-lean"),
        "registry_candidate_section": "external_sources",
        "registry_candidate": {
            "name": "brownian-motion-lean",
            "url": "https://github.com/RemyDegenne/brownian-motion",
            "local_path": "/private/tmp/lean-reuse-corpus/brownian-motion",
            "trust": "candidate search only; local Lean must verify imported uses",
        },
        "source_evidence_urls": (
            "https://github.com/RemyDegenne/brownian-motion",
            "https://reservoir.lean-lang.org/@RemyDegenne/BrownianMotion",
        ),
        "source_evidence_status": "git ls-remote verified https://github.com/RemyDegenne/brownian-motion",
    },
    {
        "target_id": "kolmogorov_extension_lean",
        "display_name": "kolmogorov_extension_lean",
        "role": "measure/probability extension candidate source",
        "aliases": ("kolmogorov_extension_lean", "kolmogorov-extension-lean"),
        "registry_candidate_section": "external_sources",
        "registry_candidate": {
            "name": "kolmogorov-extension-lean",
            "url": "https://github.com/RemyDegenne/kolmogorov_extension4",
            "local_path": "/private/tmp/lean-reuse-corpus/kolmogorov_extension4",
            "trust": "candidate search only; local Lean must verify imported uses",
        },
        "source_evidence_urls": (
            "https://github.com/RemyDegenne/kolmogorov_extension4",
            "https://reservoir.lean-lang.org/@RemyDegenne/KolmogorovExtension",
        ),
        "source_evidence_status": "git ls-remote verified https://github.com/RemyDegenne/kolmogorov_extension4",
    },
    {
        "target_id": "scilean_calculus",
        "display_name": "SciLean calculus",
        "role": "calculus/analysis automation candidate source",
        "aliases": ("scilean_calculus", "scilean-calculus", "scilean"),
        "registry_candidate_section": "external_sources",
        "registry_candidate": {
            "name": "scilean-calculus",
            "url": "https://github.com/lecopivo/SciLean",
            "local_path": "/private/tmp/lean-reuse-corpus/SciLean",
            "trust": "candidate search only; local Lean must verify imported uses",
        },
        "source_evidence_urls": (
            "https://github.com/lecopivo/SciLean",
            "https://reservoir.lean-lang.org/@CSPaulson/Scilean",
        ),
        "source_evidence_status": "git ls-remote verified https://github.com/lecopivo/SciLean",
    },
)

SOURCE_COVERAGE_BOUNDARY = (
    "Target Lean source coverage is retrieval-planning evidence only, not Lean "
    "proof evidence. A source hit can suggest premises, but theorem status "
    "changes only after local Lean/AXLE kernel verification."
)


def audit_lean_rag_package(
    out_dir: Path,
    *,
    package_root: Path | str | None = None,
    db_dir: Path | str | None = None,
) -> dict[str, object]:
    """Audit the shared `EmpericalProcessLEAN/lean_rag` package contract.

    This is deliberately read-only: generated SQLite/JSONL indexes are cache
    artifacts, while the package knowledgebase and scripts define the reusable
    contract that AI-Statistician should monitor across proof threads.
    """

    explicit_root = Path(package_root).expanduser() if package_root else _env_package_root()
    root = _resolve_package_root(explicit_root)
    required = explicit_root is not None
    available = root is not None

    file_rows = _required_file_rows(root) if root else []
    source_registry = _load_source_registry(root) if root else {}
    seed_query_payload = _load_seed_queries(root) if root else _empty_seed_query_payload()
    script_capabilities = _script_capabilities(root) if root else {}
    graph_manifest = _load_shared_graph_manifest(root, db_dir) if root else _empty_graph_manifest(db_dir)
    git_payload = _git_metadata(root) if root else {}

    registry_policy = dict(source_registry.get("policy", {}) or {})
    local_sources = list(source_registry.get("local_sources", []) or [])
    external_sources = list(source_registry.get("external_sources", []) or [])
    target_source_coverage = _target_source_coverage(
        local_sources=local_sources,
        external_sources=external_sources,
        git_payload=git_payload,
    )
    generated_outputs = dict(source_registry.get("generated_outputs", {}) or {})
    required_files_present = bool(file_rows) and all(bool(row["exists"]) for row in file_rows)
    registry_ok = bool(source_registry) and isinstance(source_registry.get("version"), int)
    seed_queries_ok = bool(seed_query_payload["valid"]) and int(seed_query_payload["n_queries"]) > 0
    policy_ok = (
        bool(registry_policy.get("verify_candidates_with_lean"))
        and bool(registry_policy.get("do_not_vendor_generated_indexes"))
        and registry_policy.get("refresh_dirty_checkouts") is False
    )
    contract_ok = bool(
        available
        and required_files_present
        and registry_ok
        and seed_queries_ok
        and policy_ok
        and script_capabilities.get("shared_status_reports_live_drift", False)
        and script_capabilities.get("refresh_reports_dirty_statinference_paths", False)
    )
    all_ok = contract_ok or (not required and not available)

    payload: dict[str, object] = {
        "schema_version": LEAN_RAG_PACKAGE_AUDIT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "available": available,
        "required": required,
        "all_ok": all_ok,
        "contract_ok": contract_ok,
        "package_root": str(root or explicit_root or ""),
        "discovery": {
            "explicit_root": str(explicit_root or ""),
            "candidate_roots": [str(path) for path in _candidate_roots()],
        },
        "git": git_payload,
        "required_files_present": required_files_present,
        "required_files": file_rows,
        "source_registry": {
            "version": source_registry.get("version"),
            "purpose": source_registry.get("purpose", ""),
            "n_local_sources": len(local_sources),
            "n_external_sources": len(external_sources),
            "local_source_names": _names(local_sources),
            "external_source_names": _names(external_sources),
            "candidate_search_only_sources": _names(
                row
                for row in external_sources
                if "candidate search only" in str(row.get("trust", "")).lower()
            ),
            "documentation_search_only_sources": _names(
                row
                for row in external_sources
                if "documentation search only" in str(row.get("trust", "")).lower()
            ),
            "generated_outputs": generated_outputs,
            "policy": registry_policy,
            "ok": registry_ok,
            "policy_ok": policy_ok,
        },
        "seed_queries": seed_query_payload,
        "target_source_coverage": target_source_coverage,
        "script_capabilities": script_capabilities,
        "shared_graph_manifest": graph_manifest,
        "recommended_actions": _recommended_actions(
            available=available,
            required=required,
            required_files_present=required_files_present,
            registry_ok=registry_ok,
            seed_queries_ok=seed_queries_ok,
            policy_ok=policy_ok,
            target_source_coverage=target_source_coverage,
            graph_manifest=graph_manifest,
        ),
    }
    payload["audit_fingerprint"] = stable_hash(
        {
            "available": payload["available"],
            "contract_ok": payload["contract_ok"],
            "git": payload["git"],
            "source_registry": payload["source_registry"],
            "seed_queries": {
                "n_queries": seed_query_payload["n_queries"],
                "lanes": seed_query_payload["lanes"],
            },
            "target_source_coverage": target_source_coverage,
            "shared_graph_manifest": payload["shared_graph_manifest"],
        }
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lean_rag_package_audit_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "lean_rag_package_audit.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def stage_lean_rag_source_registry_expansion(
    out_dir: Path,
    *,
    package_root: Path | str | None = None,
    db_dir: Path | str | None = None,
) -> dict[str, object]:
    """Write a staged source-registry expansion plan from package-audit candidates.

    This does not mutate the `lean_rag` package. It writes a proposed
    `source_registry.json` and a manifest that can be reviewed before a clean
    checkout refresh. Staged entries are retrieval candidates only; theorem
    status still changes only after local Lean/AXLE verification.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    audit_dir = out_dir / "lean_rag_package_audit"
    audit_payload = audit_lean_rag_package(
        audit_dir,
        package_root=package_root,
        db_dir=db_dir,
    )
    root = Path(str(audit_payload.get("package_root", ""))).expanduser()
    source_registry = _load_source_registry(root) if root.exists() else {}
    staged_registry = json.loads(json.dumps(source_registry, default=str)) if source_registry else {}
    coverage_before = dict(audit_payload.get("target_source_coverage", {}) or {})
    candidates = list(coverage_before.get("registry_expansion_candidates", []) or [])
    rows = _stage_registry_candidates(staged_registry, candidates)
    local_sources = list(staged_registry.get("local_sources", []) or [])
    external_sources = list(staged_registry.get("external_sources", []) or [])
    coverage_after = _target_source_coverage(
        local_sources=local_sources,
        external_sources=external_sources,
        git_payload=dict(audit_payload.get("git", {}) or {}),
    )
    staged_rows = [row for row in rows if row.get("status") == "staged"]
    invalid_rows = [row for row in rows if row.get("status") == "invalid"]
    already_present_rows = [row for row in rows if row.get("status") == "already_present"]
    clone_commands = _registry_clone_commands(staged_rows)
    payload: dict[str, object] = {
        "schema_version": LEAN_RAG_SOURCE_REGISTRY_EXPANSION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "package_root": str(root if root.exists() else audit_payload.get("package_root", "")),
        "source_registry_path": str(root / "knowledgebase" / "source_registry.json")
        if root.exists()
        else "",
        "source_registry_fingerprint_before": stable_hash(source_registry),
        "staged_source_registry_fingerprint": stable_hash(staged_registry),
        "lean_rag_package_audit_manifest": str(
            audit_dir / "lean_rag_package_audit_manifest.json"
        ),
        "package_contract_ok": bool(audit_payload.get("contract_ok")),
        "all_ok": bool(audit_payload.get("all_ok")) and not invalid_rows and bool(source_registry),
        "stage_ready": bool(source_registry) and not invalid_rows and bool(staged_rows),
        "n_candidates": len(candidates),
        "n_staged": len(staged_rows),
        "n_already_present": len(already_present_rows),
        "n_invalid": len(invalid_rows),
        "target_source_coverage_before": {
            "n_targets": coverage_before.get("n_targets", 0),
            "n_present": coverage_before.get("n_present", 0),
            "n_missing": coverage_before.get("n_missing", 0),
            "missing_target_ids": coverage_before.get("missing_target_ids", []),
        },
        "target_source_coverage_after": {
            "n_targets": coverage_after.get("n_targets", 0),
            "n_present": coverage_after.get("n_present", 0),
            "n_missing": coverage_after.get("n_missing", 0),
            "missing_target_ids": coverage_after.get("missing_target_ids", []),
        },
        "rows": rows,
        "clone_commands": clone_commands,
        "acceptance_gate": (
            "Review staged_source_registry.json, clone or refresh only clean checkouts, "
            "rebuild the external reuse index, and verify concrete reused declarations "
            "with local Lean or AXLE before promoting proof status."
        ),
        "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
        "staged_source_registry": str(out_dir / "staged_source_registry.json"),
        "source_registry_delta": str(out_dir / "source_registry_delta.json"),
    }
    (out_dir / "staged_source_registry.json").write_text(
        json.dumps(staged_registry, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "source_registry_delta.json").write_text(
        json.dumps({"rows": rows, "clone_commands": clone_commands}, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "source_registry_expansion_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "source_registry_expansion.md").write_text(
        _source_registry_expansion_markdown(payload),
        encoding="utf-8",
    )
    return payload


def preflight_lean_rag_source_registry_expansion(
    out_dir: Path,
    *,
    expansion_manifest: Path | str,
) -> dict[str, object]:
    """Validate local readiness for a staged Lean RAG source expansion.

    This is read-only. Missing Git-backed source checkouts are not errors for
    registry application, but they prevent external index refresh readiness.
    Dirty or remote-mismatched existing checkouts are hard blockers.
    """

    manifest_path = Path(expansion_manifest).expanduser()
    try:
        expansion_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        expansion_payload = {}
    package_root = Path(str(expansion_payload.get("package_root", ""))).expanduser()
    package_git = _package_git_metadata_for_preflight(package_root) if package_root.exists() else {}
    indexer_support = _registry_indexer_support(package_root) if package_root.exists() else {}
    rows = [
        _preflight_registry_row(row, indexer_support=indexer_support)
        for row in expansion_payload.get("rows", []) or []
        if isinstance(row, dict)
    ]
    counts = _preflight_counts(rows)
    source_registry_apply_ready = bool(
        expansion_payload.get("stage_ready")
        and package_root.exists()
        and not bool(package_git.get("dirty", True))
        and counts["n_hard_blockers"] == 0
    )
    external_refresh_ready = bool(
        source_registry_apply_ready
        and counts["n_clone_required"] == 0
        and counts["n_present_or_local"] == counts["n_rows"]
        and counts["n_indexer_unsupported"] == 0
    )
    clone_commands = [
        dict(row)
        for row in expansion_payload.get("clone_commands", []) or []
        if isinstance(row, dict)
    ]
    payload: dict[str, object] = {
        "schema_version": LEAN_RAG_SOURCE_EXPANSION_PREFLIGHT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expansion_manifest": str(manifest_path),
        "package_root": str(package_root if package_root.exists() else ""),
        "package_git": package_git,
        "package_clean": bool(package_root.exists()) and not bool(package_git.get("dirty", True)),
        "source_registry_apply_ready": source_registry_apply_ready,
        "external_refresh_ready": external_refresh_ready,
        "n_rows": counts["n_rows"],
        "n_present_clean_git": counts["n_present_clean_git"],
        "n_present_local_path": counts["n_present_local_path"],
        "n_clone_required": counts["n_clone_required"],
        "n_dirty_git": counts["n_dirty_git"],
        "n_remote_mismatch": counts["n_remote_mismatch"],
        "n_missing_local_path": counts["n_missing_local_path"],
        "n_non_git_destination_exists": counts["n_non_git_destination_exists"],
        "n_indexer_supported": counts["n_indexer_supported"],
        "n_indexer_unsupported": counts["n_indexer_unsupported"],
        "n_hard_blockers": counts["n_hard_blockers"],
        "indexer_support": indexer_support,
        "rows": rows,
        "clone_commands": clone_commands,
        "recommended_actions": _preflight_recommended_actions(
            source_registry_apply_ready=source_registry_apply_ready,
            external_refresh_ready=external_refresh_ready,
            rows=rows,
            clone_commands=clone_commands,
        ),
        "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "source_registry_expansion_preflight_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "source_registry_expansion_preflight.md").write_text(
        _source_registry_expansion_preflight_markdown(payload),
        encoding="utf-8",
    )
    return payload


def apply_lean_rag_source_registry_expansion(
    out_dir: Path,
    *,
    expansion_manifest: Path | str,
    preflight_manifest: Path | str | None = None,
    dry_run: bool = True,
) -> dict[str, object]:
    """Apply a reviewed staged Lean RAG source registry with safety gates.

    The default dry-run mode is read-only. A real apply requires a clean
    preflight, an unchanged source_registry.json fingerprint, and an explicit
    caller opt-in via ``dry_run=False``.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(expansion_manifest).expanduser()
    expansion_payload = _load_json_object(manifest_path)
    preflight_payload = (
        _load_json_object(Path(preflight_manifest).expanduser())
        if preflight_manifest
        else preflight_lean_rag_source_registry_expansion(
            out_dir / "preflight",
            expansion_manifest=manifest_path,
        )
    )
    source_registry_path = _manifest_path(
        expansion_payload.get("source_registry_path", ""),
        base_dir=manifest_path.parent,
    )
    staged_registry_path = _manifest_path(
        expansion_payload.get("staged_source_registry", ""),
        base_dir=manifest_path.parent,
    )
    current_registry = _load_json_object(source_registry_path)
    staged_registry = _load_json_object(staged_registry_path)
    current_fingerprint = stable_hash(current_registry) if current_registry else ""
    staged_fingerprint = stable_hash(staged_registry) if staged_registry else ""
    expected_current_fingerprint = str(
        expansion_payload.get("source_registry_fingerprint_before", "")
    )
    expected_staged_fingerprint = str(
        expansion_payload.get("staged_source_registry_fingerprint", "")
    )
    errors: list[str] = []
    warnings: list[str] = []
    if not expansion_payload.get("stage_ready"):
        errors.append("expansion manifest is not stage_ready")
    if not preflight_payload.get("source_registry_apply_ready"):
        errors.append("preflight does not mark source_registry_apply_ready")
    if not source_registry_path.exists():
        errors.append("source_registry_path does not exist")
    if not staged_registry_path.exists():
        errors.append("staged_source_registry does not exist")
    if not expected_current_fingerprint:
        errors.append("expansion manifest lacks source_registry_fingerprint_before; restage before apply")
    elif current_fingerprint != expected_current_fingerprint:
        errors.append("source_registry.json changed after staging; restage before apply")
    if not expected_staged_fingerprint:
        errors.append("expansion manifest lacks staged_source_registry_fingerprint; restage before apply")
    elif staged_fingerprint != expected_staged_fingerprint:
        errors.append("staged_source_registry changed after staging; restage before apply")
    _validate_staged_registry_policy(staged_registry, errors=errors)

    apply_ready = not errors
    applied = False
    backup_path = out_dir / "source_registry.before_apply.json"
    if apply_ready and not dry_run:
        backup_path.write_text(
            json.dumps(current_registry, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        source_registry_path.write_text(
            json.dumps(staged_registry, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        applied = True
    elif apply_ready:
        warnings.append("dry_run=True; source_registry.json was not modified")

    payload: dict[str, object] = {
        "schema_version": LEAN_RAG_SOURCE_REGISTRY_APPLY_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "apply_ready": apply_ready,
        "applied": applied,
        "expansion_manifest": str(manifest_path),
        "preflight_manifest": str(preflight_manifest or out_dir / "preflight"),
        "source_registry_path": str(source_registry_path),
        "staged_source_registry": str(staged_registry_path),
        "source_registry_fingerprint_before_expected": expected_current_fingerprint,
        "source_registry_fingerprint_before_actual": current_fingerprint,
        "staged_source_registry_fingerprint_expected": expected_staged_fingerprint,
        "staged_source_registry_fingerprint_actual": staged_fingerprint,
        "source_registry_fingerprint_after": stable_hash(staged_registry)
        if applied
        else current_fingerprint,
        "backup_path": str(backup_path) if applied else "",
        "n_staged": expansion_payload.get("n_staged", 0),
        "target_source_coverage_before": expansion_payload.get(
            "target_source_coverage_before", {}
        ),
        "target_source_coverage_after": expansion_payload.get(
            "target_source_coverage_after", {}
        ),
        "errors": errors,
        "warnings": warnings,
        "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
    }
    (out_dir / "source_registry_expansion_apply_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "source_registry_expansion_apply.md").write_text(
        _source_registry_expansion_apply_markdown(payload),
        encoding="utf-8",
    )
    return payload


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _manifest_path(value: object, *, base_dir: Path) -> Path:
    raw = str(value or "")
    path = Path(raw).expanduser()
    if path.is_absolute() or path.exists():
        return path
    candidate = base_dir / path.name
    if candidate.exists():
        return candidate
    return path


def _validate_staged_registry_policy(
    staged_registry: dict[str, object],
    *,
    errors: list[str],
) -> None:
    if not staged_registry:
        errors.append("staged source registry is empty or unreadable")
        return
    policy = dict(staged_registry.get("policy", {}) or {})
    if policy.get("verify_candidates_with_lean") is not True:
        errors.append("staged registry policy must verify candidates with Lean")
    if policy.get("do_not_vendor_generated_indexes") is not True:
        errors.append("staged registry policy must not vendor generated indexes")
    if policy.get("refresh_dirty_checkouts") is not False:
        errors.append("staged registry policy must refuse dirty checkout refreshes")


def _env_package_root() -> Path | None:
    raw = os.environ.get("AI_STATISTICIAN_LEAN_RAG_PACKAGE_ROOT", "").strip()
    return Path(raw).expanduser() if raw else None


def _resolve_package_root(explicit_root: Path | None) -> Path | None:
    candidates = (explicit_root,) if explicit_root else _candidate_roots()
    for candidate in candidates:
        if candidate is None:
            continue
        path = candidate.expanduser()
        if _looks_like_package_root(path):
            return path.resolve()
    return None


def _candidate_roots() -> tuple[Path, ...]:
    cwd = Path.cwd()
    home = Path.home()
    return (
        cwd / "lean_rag",
        cwd.parent / "EmpericalProcessLEAN" / "lean_rag",
        cwd.parent / "EmpiricalProcessLEAN" / "lean_rag",
        home / "EmpericalProcessLEAN" / "lean_rag",
        home / "EmpiricalProcessLEAN" / "lean_rag",
        Path("/tmp/empirical_process_lean_rag_latest/lean_rag"),
        Path("/tmp/empirical_process_lean_rag/lean_rag"),
    )


def _looks_like_package_root(path: Path) -> bool:
    return (
        path.exists()
        and path.is_dir()
        and (path / "knowledgebase" / "source_registry.json").exists()
        and (path / "scripts" / "shared_proof_retrieval.py").exists()
    )


def _required_file_rows(root: Path) -> list[dict[str, object]]:
    return [
        {
            "path": rel_path,
            "exists": (root / rel_path).exists(),
            "bytes": (root / rel_path).stat().st_size if (root / rel_path).exists() else 0,
        }
        for rel_path in REQUIRED_PACKAGE_FILES
    ]


def _load_source_registry(root: Path) -> dict[str, Any]:
    path = root / "knowledgebase" / "source_registry.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_seed_queries(root: Path) -> dict[str, object]:
    path = root / "knowledgebase" / "seed_queries.jsonl"
    rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {
            **_empty_seed_query_payload(),
            "errors": [{"line": 0, "error": str(exc)}],
        }
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_number, "error": str(exc)})
            continue
        if not isinstance(row, dict):
            errors.append({"line": line_number, "error": "row is not an object"})
            continue
        commands = row.get("commands", [])
        if not isinstance(commands, list) or not all(isinstance(command, str) for command in commands):
            errors.append({"line": line_number, "error": "commands must be a string list"})
            continue
        rows.append(
            {
                "lane": str(row.get("lane", "")),
                "goal": str(row.get("goal", "")),
                "commands": tuple(commands),
                "uses_graph_context": any("--with-graph-context" in command for command in commands),
                "uses_external_reuse": any("lean_reuse_corpus_search.py" in command for command in commands),
            }
        )
    lanes = tuple(sorted({str(row["lane"]) for row in rows if row.get("lane")}))
    return {
        "valid": not errors and bool(rows),
        "n_queries": len(rows),
        "lanes": lanes,
        "n_lanes": len(lanes),
        "rows": rows,
        "errors": errors,
        "all_use_packaged_scripts": bool(rows)
        and all(
            all("lean_rag/scripts/" in command for command in row["commands"])
            for row in rows
        ),
    }


def _empty_seed_query_payload() -> dict[str, object]:
    return {
        "valid": False,
        "n_queries": 0,
        "lanes": (),
        "n_lanes": 0,
        "rows": [],
        "errors": [],
        "all_use_packaged_scripts": False,
    }


def _target_source_coverage(
    *,
    local_sources: list[object],
    external_sources: list[object],
    git_payload: dict[str, object],
) -> dict[str, object]:
    local_names = _source_name_rows(local_sources)
    external_names = _source_name_rows(external_sources)
    all_names = (*local_names, *external_names)
    normalized_names = {row["normalized"]: row for row in all_names}
    git_evidence = " ".join(
        str(git_payload.get(key, ""))
        for key in ("repo_root", "remote", "branch")
    )
    normalized_git_evidence = _normalize_source_name(git_evidence)
    rows: list[dict[str, object]] = []
    for target in TARGET_LEAN_SOURCE_COVERAGE:
        aliases = tuple(str(alias) for alias in target.get("aliases", ()) or ())
        normalized_aliases = {_normalize_source_name(alias) for alias in aliases}
        matched_rows = [
            row for key, row in normalized_names.items() if key in normalized_aliases
        ]
        repository_match = (
            str(target.get("target_id")) == "empirical_process_lean"
            and any(alias in normalized_git_evidence for alias in normalized_aliases)
        )
        present = bool(matched_rows) or repository_match
        evidence_names = tuple(sorted({str(row["name"]) for row in matched_rows}))
        evidence_scope = "registry"
        if repository_match and not evidence_names:
            evidence_names = (str(git_payload.get("remote", "") or git_payload.get("repo_root", "")),)
            evidence_scope = "package_git_remote"
        elif repository_match:
            evidence_scope = "registry_and_package_git_remote"
        registry_candidate = dict(target.get("registry_candidate", {}) or {})
        rows.append(
            {
                "target_id": str(target.get("target_id", "")),
                "display_name": str(target.get("display_name", "")),
                "role": str(target.get("role", "")),
                "aliases": aliases,
                "present": present,
                "evidence_scope": evidence_scope if present else "missing",
                "matched_source_names": evidence_names,
                "registry_candidate_section": str(target.get("registry_candidate_section", "")),
                "registry_candidate": registry_candidate,
                "source_evidence_urls": tuple(
                    str(url) for url in target.get("source_evidence_urls", ()) or ()
                ),
                "source_evidence_status": str(target.get("source_evidence_status", "")),
                "recommended_action": ""
                if present
                else (
                    "Add this corpus to lean_rag/knowledgebase/source_registry.json "
                    "as candidate-search-only or documentation-search-only source, "
                    "then rebuild the external reuse index on clean checkouts."
                ),
                "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
            }
        )
    missing = tuple(row["target_id"] for row in rows if not row["present"])
    present = tuple(row["target_id"] for row in rows if row["present"])
    registry_expansion_candidates = _registry_expansion_candidates(rows)
    return {
        "n_targets": len(rows),
        "n_present": len(present),
        "n_missing": len(missing),
        "coverage_ok": not missing,
        "present_target_ids": present,
        "missing_target_ids": missing,
        "n_registry_expansion_candidates": len(registry_expansion_candidates),
        "registry_expansion_candidates": registry_expansion_candidates,
        "rows": rows,
        "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
    }


def _registry_expansion_candidates(rows: list[dict[str, object]]) -> tuple[dict[str, object], ...]:
    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        if row.get("present"):
            continue
        candidate = dict(row.get("registry_candidate", {}) or {})
        section = str(row.get("registry_candidate_section", "") or "")
        if not candidate or not section:
            continue
        key = stable_hash({"section": section, "candidate": candidate})
        item = grouped.setdefault(
            key,
            {
                "candidate_id": key,
                "target_ids": [],
                "section": section,
                "entry": candidate,
                "source_evidence_urls": [],
                "source_evidence_statuses": [],
                "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
                "acceptance_gate": (
                    "Stage in source_registry.json, clone or refresh only clean checkouts, "
                    "rebuild the external reuse index, then verify any reused theorem with "
                    "local Lean or AXLE before upgrading proof status."
                ),
            },
        )
        item["target_ids"].append(str(row.get("target_id", "")))
        item["source_evidence_urls"].extend(
            str(url) for url in row.get("source_evidence_urls", []) or []
        )
        status = str(row.get("source_evidence_status", "") or "")
        if status:
            item["source_evidence_statuses"].append(status)
    result: list[dict[str, object]] = []
    for item in grouped.values():
        result.append(
            {
                **item,
                "target_ids": tuple(sorted(set(str(target) for target in item["target_ids"]))),
                "source_evidence_urls": tuple(
                    sorted(set(str(url) for url in item["source_evidence_urls"]))
                ),
                "source_evidence_statuses": tuple(
                    sorted(set(str(status) for status in item["source_evidence_statuses"]))
                ),
            }
        )
    return tuple(sorted(result, key=lambda item: str(dict(item["entry"]).get("name", ""))))


def _stage_registry_candidates(
    staged_registry: dict[str, object],
    candidates: list[object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    existing_names = _registry_existing_source_names(staged_registry)
    for candidate in candidates:
        if not isinstance(candidate, dict):
            rows.append(
                {
                    "status": "invalid",
                    "reason": "candidate is not an object",
                    "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
                }
            )
            continue
        section = str(candidate.get("section", ""))
        entry = dict(candidate.get("entry", {}) or {})
        name = str(entry.get("name", ""))
        normalized_name = _normalize_source_name(name)
        if section not in VALID_SOURCE_REGISTRY_SECTIONS:
            status = "invalid"
            reason = f"unsupported source_registry section: {section}"
        elif not normalized_name:
            status = "invalid"
            reason = "candidate entry is missing name"
        elif normalized_name in existing_names:
            status = "already_present"
            reason = "source name already appears in the registry"
        else:
            staged_registry.setdefault(section, [])
            if not isinstance(staged_registry[section], list):
                staged_registry[section] = []
            staged_registry[section].append(entry)
            existing_names.add(normalized_name)
            status = "staged"
            reason = ""
        rows.append(
            {
                "candidate_id": str(candidate.get("candidate_id", "")),
                "target_ids": tuple(str(item) for item in candidate.get("target_ids", []) or []),
                "section": section,
                "entry": entry,
                "status": status,
                "reason": reason,
                "source_evidence_urls": tuple(
                    str(url) for url in candidate.get("source_evidence_urls", []) or []
                ),
                "source_evidence_statuses": tuple(
                    str(status) for status in candidate.get("source_evidence_statuses", []) or []
                ),
                "acceptance_gate": str(candidate.get("acceptance_gate", "")),
                "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
            }
        )
    return rows


def _registry_existing_source_names(source_registry: dict[str, object]) -> set[str]:
    names: set[str] = set()
    for section in VALID_SOURCE_REGISTRY_SECTIONS:
        for row in source_registry.get(section, []) or []:
            if isinstance(row, dict):
                name = _normalize_source_name(str(row.get("name", "")))
                if name:
                    names.add(name)
    return names


def _registry_clone_commands(rows: list[dict[str, object]]) -> tuple[dict[str, str], ...]:
    commands: list[dict[str, str]] = []
    for row in rows:
        entry = dict(row.get("entry", {}) or {})
        url = str(entry.get("url", ""))
        local_path = str(entry.get("local_path", ""))
        if not url or not local_path:
            continue
        commands.append(
            {
                "name": str(entry.get("name", "")),
                "command": f"git clone {url} {local_path}",
                "note": "Run only when the destination is absent or intentionally refreshed in a clean checkout.",
            }
        )
    return tuple(commands)


def _preflight_registry_row(
    row: dict[str, object],
    *,
    indexer_support: dict[str, object],
) -> dict[str, object]:
    entry = dict(row.get("entry", {}) or {})
    name = str(entry.get("name", ""))
    normalized_name = _normalize_source_name(name)
    url = str(entry.get("url", ""))
    local_path = str(entry.get("local_path", ""))
    script_text = str(indexer_support.get("script_text_normalized", ""))
    indexer_supported = bool(normalized_name and normalized_name in script_text)
    path = Path(local_path).expanduser() if local_path else None
    exists = bool(path and path.exists())
    is_git = bool(path and (path / ".git").exists())
    git_dirty = False
    git_remote = ""
    git_commit = ""
    git_branch = ""
    status = "missing_local_path"
    hard_blocker = True
    reason = "candidate entry has no local_path"
    if path is not None and exists and is_git:
        git_remote = _git(path, "remote", "get-url", "origin")
        git_commit = _git(path, "rev-parse", "HEAD")
        git_branch = _git(path, "rev-parse", "--abbrev-ref", "HEAD")
        git_dirty = bool(_git(path, "status", "--short"))
        remote_ok = (not url) or _same_git_remote(git_remote, url)
        if git_dirty:
            status = "dirty_git"
            reason = "existing git checkout has local changes"
            hard_blocker = True
        elif not remote_ok:
            status = "remote_mismatch"
            reason = f"expected origin {url}, found {git_remote}"
            hard_blocker = True
        else:
            status = "present_clean_git"
            reason = ""
            hard_blocker = False
    elif path is not None and exists and url:
        status = "non_git_destination_exists"
        reason = "destination exists for a Git-backed candidate but is not a git checkout"
        hard_blocker = True
    elif path is not None and exists:
        status = "present_local_path"
        reason = ""
        hard_blocker = False
    elif path is not None and url:
        status = "clone_required"
        reason = "destination is absent and should be cloned before refreshing the external reuse index"
        hard_blocker = False
    return {
        "candidate_id": str(row.get("candidate_id", "")),
        "target_ids": tuple(str(item) for item in row.get("target_ids", []) or []),
        "name": name,
        "url": url,
        "local_path": local_path,
        "exists": exists,
        "is_git_checkout": is_git,
        "git_dirty": git_dirty,
        "git_remote": git_remote,
        "git_commit": git_commit,
        "git_branch": git_branch,
        "indexer_supported": indexer_supported,
        "indexer_support_status": "supported_by_current_scripts"
        if indexer_supported
        else "unsupported_by_current_scripts",
        "indexer_support_reason": ""
        if indexer_supported
        else "current refresh/index scripts do not mention this source name; add a script route before expecting it in the external reuse index",
        "status": status,
        "hard_blocker": hard_blocker,
        "reason": reason,
        "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
    }


def _registry_indexer_support(package_root: Path) -> dict[str, object]:
    refresh = _read_text(package_root / "scripts" / "refresh_lean_reuse_sources.py")
    indexer = _read_text(package_root / "scripts" / "external_lean_corpus_index.py")
    search = _read_text(package_root / "scripts" / "lean_reuse_corpus_search.py")
    combined = _normalize_source_name(" ".join((refresh, indexer, search)))
    return {
        "script_text_normalized": combined,
        "detection": "source names must appear in current refresh/index/search scripts",
    }


def _same_git_remote(actual: str, expected: str) -> bool:
    def normalize(value: str) -> str:
        return value.strip().removesuffix(".git")

    return normalize(actual) == normalize(expected)


def _preflight_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    statuses = [str(row.get("status", "")) for row in rows]
    return {
        "n_rows": len(rows),
        "n_present_clean_git": statuses.count("present_clean_git"),
        "n_present_local_path": statuses.count("present_local_path"),
        "n_clone_required": statuses.count("clone_required"),
        "n_dirty_git": statuses.count("dirty_git"),
        "n_remote_mismatch": statuses.count("remote_mismatch"),
        "n_missing_local_path": statuses.count("missing_local_path"),
        "n_non_git_destination_exists": statuses.count("non_git_destination_exists"),
        "n_present_or_local": statuses.count("present_clean_git")
        + statuses.count("present_local_path"),
        "n_indexer_supported": sum(1 for row in rows if row.get("indexer_supported")),
        "n_indexer_unsupported": sum(1 for row in rows if not row.get("indexer_supported")),
        "n_hard_blockers": sum(1 for row in rows if row.get("hard_blocker")),
    }


def _preflight_recommended_actions(
    *,
    source_registry_apply_ready: bool,
    external_refresh_ready: bool,
    rows: list[dict[str, object]],
    clone_commands: list[dict[str, object]],
) -> list[str]:
    actions: list[str] = []
    if not source_registry_apply_ready:
        actions.append(
            "Do not apply the staged source registry until the package checkout is clean and all hard blockers are resolved."
        )
    clone_required_names = {
        str(row.get("name", ""))
        for row in rows
        if row.get("status") == "clone_required" and row.get("name")
    }
    clone_required_commands = [
        str(row.get("command", ""))
        for row in clone_commands
        if str(row.get("name", "")) in clone_required_names and row.get("command")
    ]
    if clone_required_names and not external_refresh_ready:
        action_tail = (
            "; ".join(clone_required_commands)
            if clone_required_commands
            else ", ".join(sorted(clone_required_names))
        )
        actions.append(
            "Clone missing Git-backed candidate sources before rebuilding the external reuse index: "
            + action_tail
        )
    unsupported = [
        str(row.get("name", "")) for row in rows if not row.get("indexer_supported")
    ]
    if unsupported:
        actions.append(
            "Extend lean_rag refresh/index/search scripts before expecting staged sources in the external reuse index: "
            + ", ".join(unsupported)
        )
    dirty = [str(row.get("name", "")) for row in rows if row.get("status") == "dirty_git"]
    if dirty:
        actions.append("Commit, stash, or discard local changes in candidate checkouts: " + ", ".join(dirty))
    mismatched = [
        str(row.get("name", "")) for row in rows if row.get("status") == "remote_mismatch"
    ]
    if mismatched:
        actions.append("Resolve candidate remote mismatches before refresh: " + ", ".join(mismatched))
    if external_refresh_ready:
        actions.append(
            "All staged candidate source paths are present and clean; the external reuse index can be refreshed after applying the reviewed registry."
        )
    actions.append(
        "Treat the refreshed index as premise-search evidence only until local Lean or AXLE verifies concrete proof uses."
    )
    return actions


def _source_name_rows(rows: list[object]) -> tuple[dict[str, str], ...]:
    names: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", ""))
        if not name:
            continue
        names.append({"name": name, "normalized": _normalize_source_name(name)})
    return tuple(names)


def _normalize_source_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _script_capabilities(root: Path) -> dict[str, object]:
    shared = _read_text(root / "scripts" / "shared_proof_retrieval.py")
    refresh = _read_text(root / "scripts" / "refresh_lean_reuse_sources.py")
    external_index = _read_text(root / "scripts" / "external_lean_corpus_index.py")
    search = _read_text(root / "scripts" / "lean_reuse_corpus_search.py")
    return {
        "shared_status_command": "status_command" in shared,
        "shared_search_command": "search_command" in shared,
        "shared_deps_command": "deps_command" in shared,
        "shared_hotspots_command": "hotspots_command" in shared,
        "shared_graph_context_search": "--with-graph-context" in shared,
        "shared_no_sorry_filter": "--no-sorry" in shared,
        "shared_low_disk_guard": "--min-free-mib" in shared and "--force-low-disk" in shared,
        "shared_status_reports_live_drift": "live=" in shared and "git_ahead_behind" in shared,
        "shared_status_reports_unindexed_dirty_worktrees": "dirty_count" in shared
        and "not indexed" in shared,
        "refresh_refuses_dirty_statinference_index": "ensure_clean_statinference_for_index" in refresh,
        "refresh_reports_dirty_statinference_paths": "Dirty StatInference paths" in refresh,
        "refresh_allow_dirty_override": "--allow-dirty-statinference-index" in refresh,
        "external_index_records_dirty_metadata": "\"dirty\"" in external_index and "git_meta" in external_index,
        "external_search_skips_stale_local": "include-stale-local" in search,
    }


def _load_shared_graph_manifest(
    root: Path,
    db_dir: Path | str | None,
) -> dict[str, object]:
    source_registry = _load_source_registry(root)
    generated_outputs = dict(source_registry.get("generated_outputs", {}) or {})
    default_shared_graph = generated_outputs.get("shared_graph", "build/lean_graph")
    graph_dir = Path(db_dir).expanduser() if db_dir else root / str(default_shared_graph)
    if not graph_dir.is_absolute():
        graph_dir = root / graph_dir
    path = graph_dir / "shared_manifest.json"
    if not path.exists():
        return _empty_graph_manifest(graph_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {**_empty_graph_manifest(graph_dir), "manifest_path": str(path), "error": str(exc)}
    checkouts = list(payload.get("checkouts", []) or [])
    dirty = [
        str(row.get("name", ""))
        for row in checkouts
        if isinstance(row, dict) and row.get("dirty")
    ]
    indexed = [
        str(row.get("name", ""))
        for row in checkouts
        if isinstance(row, dict) and row.get("indexed")
    ]
    failed = [
        str(row.get("name", ""))
        for row in checkouts
        if isinstance(row, dict) and not row.get("indexed")
    ]
    return {
        "available": True,
        "manifest_path": str(path),
        "schema": payload.get("schema"),
        "project_root": payload.get("project_root", ""),
        "db_dir": payload.get("db_dir", str(graph_dir)),
        "n_checkouts": len(checkouts),
        "n_indexed_checkouts": len(indexed),
        "n_dirty_checkouts": len(dirty),
        "n_failed_checkouts": len(failed),
        "indexed_checkouts": tuple(indexed),
        "dirty_checkouts": tuple(dirty),
        "failed_checkouts": tuple(failed),
        "total_declarations": sum(_int(row.get("declarations")) for row in checkouts if isinstance(row, dict)),
        "total_declaration_edges": sum(
            _int(row.get("declaration_edges")) for row in checkouts if isinstance(row, dict)
        ),
    }


def _empty_graph_manifest(db_dir: Path | str | None) -> dict[str, object]:
    return {
        "available": False,
        "manifest_path": str(Path(db_dir).expanduser() / "shared_manifest.json") if db_dir else "",
        "schema": None,
        "project_root": "",
        "db_dir": str(db_dir or ""),
        "n_checkouts": 0,
        "n_indexed_checkouts": 0,
        "n_dirty_checkouts": 0,
        "n_failed_checkouts": 0,
        "indexed_checkouts": (),
        "dirty_checkouts": (),
        "failed_checkouts": (),
        "total_declarations": 0,
        "total_declaration_edges": 0,
    }


def _git_metadata(root: Path) -> dict[str, object]:
    repo_root = _git(root, "rev-parse", "--show-toplevel")
    return {
        "repo_root": repo_root,
        "branch": _git(root, "rev-parse", "--abbrev-ref", "HEAD"),
        "commit": _git(root, "rev-parse", "HEAD"),
        "short_commit": _git(root, "rev-parse", "--short=12", "HEAD"),
        "remote": _git(root, "remote", "get-url", "origin"),
        "dirty": bool(_git(root, "status", "--short")),
    }


def _package_git_metadata_for_preflight(root: Path) -> dict[str, object]:
    metadata = _git_metadata(root)
    repo_root = str(metadata.get("repo_root", ""))
    if not repo_root:
        return {
            "repo_root": "",
            "branch": "",
            "commit": "",
            "short_commit": "",
            "remote": "",
            "dirty": False,
            "scope": "not_git_checkout",
        }
    if (root / ".git").exists() or Path(repo_root).resolve() == root.resolve():
        return {**metadata, "scope": "package_git_checkout"}
    return {
        **metadata,
        "dirty": False,
        "scope": "nested_non_package_git_checkout",
        "parent_dirty_ignored": bool(metadata.get("dirty", False)),
    }


def _git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=30,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _recommended_actions(
    *,
    available: bool,
    required: bool,
    required_files_present: bool,
    registry_ok: bool,
    seed_queries_ok: bool,
    policy_ok: bool,
    target_source_coverage: dict[str, object],
    graph_manifest: dict[str, object],
) -> list[str]:
    actions: list[str] = []
    if not available:
        if required:
            actions.append("Fix --lean-rag-package-root or AI_STATISTICIAN_LEAN_RAG_PACKAGE_ROOT.")
        else:
            actions.append(
                "Optionally sparse-clone EmpericalProcessLEAN branch codex/rag-infra-package and point AI_STATISTICIAN_LEAN_RAG_PACKAGE_ROOT at lean_rag."
            )
        return actions
    if not required_files_present:
        actions.append("Refresh the lean_rag package checkout; required scripts/docs are missing.")
    if not registry_ok:
        actions.append("Restore knowledgebase/source_registry.json before using package policy.")
    if not seed_queries_ok:
        actions.append("Restore knowledgebase/seed_queries.jsonl so proof lanes have reusable retrieval recipes.")
    if not policy_ok:
        actions.append(
            "Align source_registry policy with Lean verification boundaries: verify candidates with Lean and do not refresh dirty checkouts."
        )
    missing_sources = tuple(target_source_coverage.get("missing_target_ids", ()) or ())
    if missing_sources:
        actions.append(
            "Expand lean_rag source coverage for missing target corpora: "
            + ", ".join(str(item) for item in missing_sources)
            + ". Treat these additions as candidate retrieval sources until local Lean verifies imported uses."
        )
    registry_candidates = tuple(
        target_source_coverage.get("registry_expansion_candidates", ()) or ()
    )
    if registry_candidates:
        names = [
            str(dict(candidate.get("entry", {}) or {}).get("name", ""))
            for candidate in registry_candidates
        ]
        actions.append(
            "Stage candidate source_registry entries for: "
            + ", ".join(name for name in names if name)
            + ". These entries improve retrieval coverage only; promotion still requires local Lean/AXLE evidence."
        )
    if not graph_manifest.get("available"):
        actions.append(
            "Run `python3 lean_rag/scripts/shared_proof_retrieval.py refresh --checkout main --no-export-main-csv` on a clean Lean tree when a fresh graph cache is needed."
        )
    if int(graph_manifest.get("n_dirty_checkouts", 0) or 0):
        actions.append(
            "Do not refresh dirty proof checkouts; verify and commit/stash them, then run a targeted shared_proof_retrieval refresh."
        )
    if int(graph_manifest.get("n_failed_checkouts", 0) or 0):
        actions.append("Inspect failed shared graph checkouts before trusting dependency-search coverage.")
    return actions


def _markdown_report(payload: dict[str, object]) -> str:
    registry = dict(payload.get("source_registry", {}) or {})
    seeds = dict(payload.get("seed_queries", {}) or {})
    coverage = dict(payload.get("target_source_coverage", {}) or {})
    graph = dict(payload.get("shared_graph_manifest", {}) or {})
    git_payload = dict(payload.get("git", {}) or {})
    lines = [
        "# Lean RAG Package Audit",
        "",
        f"- Available: `{payload.get('available')}`",
        f"- Contract OK: `{payload.get('contract_ok')}`",
        f"- Package root: `{payload.get('package_root')}`",
        f"- Git: `{git_payload.get('branch', '')}@{git_payload.get('short_commit', '')}` dirty=`{git_payload.get('dirty', '')}`",
        f"- Sources: local=`{registry.get('n_local_sources')}` external=`{registry.get('n_external_sources')}`",
        f"- Target source coverage: `{coverage.get('n_present')}/{coverage.get('n_targets')}` present; missing=`{', '.join(coverage.get('missing_target_ids', []))}`",
        f"- Registry expansion candidates: `{coverage.get('n_registry_expansion_candidates', 0)}`",
        f"- Policy: verify_candidates_with_lean=`{dict(registry.get('policy', {}) or {}).get('verify_candidates_with_lean')}` refresh_dirty_checkouts=`{dict(registry.get('policy', {}) or {}).get('refresh_dirty_checkouts')}`",
        f"- Seed lanes: `{', '.join(seeds.get('lanes', []))}`",
        f"- Shared graph manifest: available=`{graph.get('available')}` indexed=`{graph.get('n_indexed_checkouts')}` dirty=`{graph.get('n_dirty_checkouts')}`",
        "",
        "## Recommended Actions",
        "",
    ]
    actions = payload.get("recommended_actions", [])
    if actions:
        lines.extend(f"- {action}" for action in actions)
    else:
        lines.append("- No package-level action required.")
    lines.extend(["", "## Seed Queries", ""])
    for row in seeds.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(f"- `{row.get('lane')}`: {row.get('goal')}")
    lines.extend(["", "## Target Source Coverage", ""])
    lines.append(str(coverage.get("proof_evidence_boundary", SOURCE_COVERAGE_BOUNDARY)))
    lines.append("")
    for row in coverage.get("rows", []):
        if not isinstance(row, dict):
            continue
        status = "present" if row.get("present") else "missing"
        matched = ", ".join(str(item) for item in row.get("matched_source_names", [])) or "none"
        candidate = dict(row.get("registry_candidate", {}) or {})
        candidate_name = str(candidate.get("name", "")) or "none"
        lines.append(
            f"- `{row.get('target_id')}` ({status}): {row.get('display_name')} "
            f"matched={matched} candidate=`{candidate_name}`"
        )
    lines.extend(["", "## Registry Expansion Candidates", ""])
    for candidate in coverage.get("registry_expansion_candidates", []):
        if not isinstance(candidate, dict):
            continue
        entry = dict(candidate.get("entry", {}) or {})
        target_ids = ", ".join(str(item) for item in candidate.get("target_ids", []))
        lines.append(
            f"- `{entry.get('name')}` -> `{candidate.get('section')}` "
            f"targets=`{target_ids}` local_path=`{entry.get('local_path', '')}` "
            f"url=`{entry.get('url', '')}`"
        )
    return "\n".join(lines) + "\n"


def _source_registry_expansion_markdown(payload: dict[str, object]) -> str:
    before = dict(payload.get("target_source_coverage_before", {}) or {})
    after = dict(payload.get("target_source_coverage_after", {}) or {})
    lines = [
        "# Lean RAG Source Registry Expansion",
        "",
        f"- Package root: `{payload.get('package_root', '')}`",
        f"- Package contract ok: `{payload.get('package_contract_ok')}`",
        f"- Stage ready: `{payload.get('stage_ready')}`",
        f"- Candidates: `{payload.get('n_candidates')}` staged=`{payload.get('n_staged')}` already_present=`{payload.get('n_already_present')}` invalid=`{payload.get('n_invalid')}`",
        f"- Target coverage before: `{before.get('n_present')}/{before.get('n_targets')}` missing=`{', '.join(before.get('missing_target_ids', []))}`",
        f"- Target coverage after: `{after.get('n_present')}/{after.get('n_targets')}` missing=`{', '.join(after.get('missing_target_ids', []))}`",
        "",
        str(payload.get("proof_evidence_boundary", SOURCE_COVERAGE_BOUNDARY)),
        "",
        "## Staged Entries",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        entry = dict(row.get("entry", {}) or {})
        targets = ", ".join(str(item) for item in row.get("target_ids", []))
        lines.append(
            f"- `{entry.get('name', '')}` status=`{row.get('status')}` "
            f"section=`{row.get('section')}` targets=`{targets}`"
        )
    lines.extend(["", "## Clone Commands", ""])
    for row in payload.get("clone_commands", []):
        if not isinstance(row, dict):
            continue
        lines.append(f"- `{row.get('name', '')}`: `{row.get('command', '')}`")
    return "\n".join(lines) + "\n"


def _source_registry_expansion_preflight_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Lean RAG Source Registry Expansion Preflight",
        "",
        f"- Expansion manifest: `{payload.get('expansion_manifest', '')}`",
        f"- Package root: `{payload.get('package_root', '')}`",
        f"- Package clean: `{payload.get('package_clean')}`",
        f"- Source registry apply ready: `{payload.get('source_registry_apply_ready')}`",
        f"- External refresh ready: `{payload.get('external_refresh_ready')}`",
        f"- Rows: `{payload.get('n_rows')}` clone_required=`{payload.get('n_clone_required')}` indexer_unsupported=`{payload.get('n_indexer_unsupported')}` hard_blockers=`{payload.get('n_hard_blockers')}`",
        "",
        str(payload.get("proof_evidence_boundary", SOURCE_COVERAGE_BOUNDARY)),
        "",
        "## Candidate Paths",
        "",
    ]
    for row in payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            f"- `{row.get('name', '')}` status=`{row.get('status')}` "
            f"indexer=`{row.get('indexer_support_status')}` "
            f"path=`{row.get('local_path', '')}` reason=`{row.get('reason', '')}`"
        )
    lines.extend(["", "## Recommended Actions", ""])
    for action in payload.get("recommended_actions", []):
        lines.append(f"- {action}")
    return "\n".join(lines) + "\n"


def _source_registry_expansion_apply_markdown(payload: dict[str, object]) -> str:
    before = dict(payload.get("target_source_coverage_before", {}) or {})
    after = dict(payload.get("target_source_coverage_after", {}) or {})
    lines = [
        "# Lean RAG Source Registry Expansion Apply",
        "",
        f"- Dry run: `{payload.get('dry_run')}`",
        f"- Apply ready: `{payload.get('apply_ready')}`",
        f"- Applied: `{payload.get('applied')}`",
        f"- Expansion manifest: `{payload.get('expansion_manifest', '')}`",
        f"- Source registry: `{payload.get('source_registry_path', '')}`",
        f"- Staged registry: `{payload.get('staged_source_registry', '')}`",
        f"- Staged rows: `{payload.get('n_staged')}`",
        f"- Target coverage before: `{before.get('n_present')}/{before.get('n_targets')}`",
        f"- Target coverage after: `{after.get('n_present')}/{after.get('n_targets')}`",
        f"- Backup path: `{payload.get('backup_path', '')}`",
        "",
        "## Fingerprints",
        "",
        f"- Current expected: `{payload.get('source_registry_fingerprint_before_expected', '')}`",
        f"- Current actual: `{payload.get('source_registry_fingerprint_before_actual', '')}`",
        f"- Staged expected: `{payload.get('staged_source_registry_fingerprint_expected', '')}`",
        f"- Staged actual: `{payload.get('staged_source_registry_fingerprint_actual', '')}`",
        f"- After: `{payload.get('source_registry_fingerprint_after', '')}`",
        "",
        str(payload.get("proof_evidence_boundary", SOURCE_COVERAGE_BOUNDARY)),
        "",
        "## Errors",
        "",
    ]
    for error in payload.get("errors", []):
        lines.append(f"- {error}")
    if not payload.get("errors"):
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    for warning in payload.get("warnings", []):
        lines.append(f"- {warning}")
    if not payload.get("warnings"):
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _names(rows: Any) -> tuple[str, ...]:
    return tuple(str(row.get("name", "")) for row in rows if isinstance(row, dict) and row.get("name"))


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
