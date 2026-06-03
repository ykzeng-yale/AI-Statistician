from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .lean_rag_dependency import LeanRagDependencyRetriever


LEAN_RAG_DEPENDENCY_HEALTH_SCHEMA_VERSION = 1


def audit_lean_rag_dependency_health(
    out_dir: Path,
    *,
    requested_db_path: str | Path | None = None,
    active_db_path: str | Path | None = None,
    auto_discovered: bool = False,
) -> dict[str, object]:
    """Record dependency-graph DB health and safe fallback status.

    This audit is intentionally non-blocking when a requested DB is missing or
    unhealthy. The research system can fall back to local formal-source search,
    but the reason must be visible in manifests and RAG handoffs.
    """

    requested = Path(requested_db_path).expanduser() if requested_db_path else None
    active = Path(active_db_path).expanduser() if active_db_path else None
    requested_health = _health_for_path(requested)
    active_health = _health_for_path(active) if active is not None else {}
    requested_healthy = bool(requested_health.get("all_ok", False))
    active_enabled = bool(active and active_health.get("all_ok", False))
    fallback_used = bool(requested and not active_enabled and not requested_healthy)
    fallback_reason = _fallback_reason(
        requested=requested,
        requested_health=requested_health,
        active_enabled=active_enabled,
    )
    status = (
        "active_healthy"
        if active_enabled
        else "requested_healthy_not_attached"
        if requested_healthy
        else "fallback_requested_db_unhealthy"
        if fallback_used
        else "not_configured"
    )
    payload: dict[str, object] = {
        "schema_version": LEAN_RAG_DEPENDENCY_HEALTH_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requested_db_path": str(requested or ""),
        "active_db_path": str(active or ""),
        "auto_discovered": auto_discovered,
        "active_enabled": active_enabled,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "health_status": status,
        "requested_health": requested_health,
        "active_health": active_health,
        "safe_for_audit": True,
        "all_ok": True,
        "limitations": [
            "dependency DB health is retrieval infrastructure evidence, not theorem proof evidence",
            "falling back to local formal-source search preserves audit safety but weakens hybrid Lean-RAG coverage",
            "a requested unhealthy DB must be rebuilt before dependency-graph retrieval can be claimed active",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "lean_rag_dependency_health_manifest.json").write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    (out_dir / "lean_rag_dependency_health.md").write_text(
        _markdown_report(payload),
        encoding="utf-8",
    )
    return payload


def _health_for_path(path: Path | None) -> dict[str, object]:
    if path is None:
        return {
            "db_path": "",
            "exists": False,
            "all_ok": False,
            "integrity_check_ok": False,
            "fts_probe_ok": False,
            "health_error": "not configured",
        }
    try:
        return LeanRagDependencyRetriever(path).health_report()
    except Exception as exc:
        return {
            "db_path": str(path),
            "exists": path.exists(),
            "all_ok": False,
            "integrity_check_ok": False,
            "fts_probe_ok": False,
            "health_error": f"{type(exc).__name__}: {exc}",
        }


def _fallback_reason(
    *,
    requested: Path | None,
    requested_health: dict[str, object],
    active_enabled: bool,
) -> str:
    if requested is None:
        return ""
    if active_enabled:
        return ""
    if not requested.exists():
        return "requested DB path does not exist"
    if requested_health.get("fts_probe_error"):
        return str(requested_health.get("fts_probe_error"))
    if requested_health.get("integrity_check_result") and not requested_health.get("integrity_check_ok"):
        return str(requested_health.get("integrity_check_result"))
    if not requested_health.get("schema_has_declarations"):
        return "requested DB missing declarations table"
    if not (requested_health.get("schema_has_decl_fts") or requested_health.get("schema_has_decl_fts_plain")):
        return "requested DB missing FTS table"
    return "requested DB failed dependency retrieval health check"


def _markdown_report(payload: dict[str, object]) -> str:
    requested = dict(payload.get("requested_health", {}) or {})
    active = dict(payload.get("active_health", {}) or {})
    lines = [
        "# Lean RAG Dependency Health",
        "",
        f"- Status: `{payload.get('health_status')}`",
        f"- Requested DB: `{payload.get('requested_db_path')}`",
        f"- Active DB: `{payload.get('active_db_path')}`",
        f"- Active enabled: {payload.get('active_enabled')}",
        f"- Fallback used: {payload.get('fallback_used')}",
        f"- Fallback reason: {payload.get('fallback_reason')}",
        "",
        "## Requested DB",
        "",
        f"- Exists: {requested.get('exists')}",
        f"- Integrity OK: {requested.get('integrity_check_ok')}",
        f"- FTS probe OK: {requested.get('fts_probe_ok')}",
        f"- All OK: {requested.get('all_ok')}",
        f"- FTS probe error: {requested.get('fts_probe_error', '')}",
        "",
        "## Active DB",
        "",
        f"- Exists: {active.get('exists')}",
        f"- Integrity OK: {active.get('integrity_check_ok')}",
        f"- FTS probe OK: {active.get('fts_probe_ok')}",
        f"- All OK: {active.get('all_ok')}",
        "",
        "## Honesty Boundary",
        "",
    ]
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
