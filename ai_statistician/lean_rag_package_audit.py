from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fingerprint import stable_hash


LEAN_RAG_PACKAGE_AUDIT_SCHEMA_VERSION = 1

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
        "aliases": ("formal_slt", "formal-slt"),
    },
    {
        "target_id": "lean_rademacher",
        "display_name": "lean_rademacher",
        "role": "Rademacher-complexity candidate source",
        "aliases": ("lean_rademacher", "lean-rademacher"),
    },
    {
        "target_id": "lean_machine_learning_lml",
        "display_name": "lean_machine_learning_lml",
        "role": "machine-learning Lean candidate source",
        "aliases": ("lean_machine_learning_lml", "lean-machine-learning-lml", "lml"),
    },
    {
        "target_id": "brownian_motion_lean",
        "display_name": "brownian_motion_lean",
        "role": "stochastic-process candidate source",
        "aliases": ("brownian_motion_lean", "brownian-motion-lean"),
    },
    {
        "target_id": "kolmogorov_extension_lean",
        "display_name": "kolmogorov_extension_lean",
        "role": "measure/probability extension candidate source",
        "aliases": ("kolmogorov_extension_lean", "kolmogorov-extension-lean"),
    },
    {
        "target_id": "scilean_calculus",
        "display_name": "SciLean calculus",
        "role": "calculus/analysis automation candidate source",
        "aliases": ("scilean_calculus", "scilean-calculus", "scilean"),
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
        rows.append(
            {
                "target_id": str(target.get("target_id", "")),
                "display_name": str(target.get("display_name", "")),
                "role": str(target.get("role", "")),
                "aliases": aliases,
                "present": present,
                "evidence_scope": evidence_scope if present else "missing",
                "matched_source_names": evidence_names,
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
    return {
        "n_targets": len(rows),
        "n_present": len(present),
        "n_missing": len(missing),
        "coverage_ok": not missing,
        "present_target_ids": present,
        "missing_target_ids": missing,
        "rows": rows,
        "proof_evidence_boundary": SOURCE_COVERAGE_BOUNDARY,
    }


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
        lines.append(
            f"- `{row.get('target_id')}` ({status}): {row.get('display_name')} "
            f"matched={matched}"
        )
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
