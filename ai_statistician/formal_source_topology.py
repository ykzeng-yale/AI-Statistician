from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Sequence


FORMAL_SOURCE_TOPOLOGY_POLICY_PATH = (
    Path(__file__).resolve().parent / "policies" / "formal_source_topology.json"
)
FORMAL_SOURCE_TOPOLOGY_EVIDENCE_STATUS = (
    "SOURCE_TOPOLOGY_AND_TOOLCHAIN_RELATION_NOT_PROOF_EVIDENCE"
)
_HEX_REVISION_RE = re.compile(r"^[0-9a-f]{7,64}$")


@dataclass(frozen=True)
class FormalSourceTopology:
    source_id: str
    aliases: tuple[str, ...]
    role: str
    relation_to_active_project: str
    reuse_policy: str
    topology_id: str
    is_active_project: bool = False
    compatibility_status: str = "unknown"
    source_lean_toolchain: str = ""
    source_mathlib_revision: str = ""
    active_lean_toolchain: str = ""
    active_mathlib_revision: str = ""
    identity_basis: tuple[str, ...] = ()

    def as_prompt_payload(self) -> dict[str, object]:
        return {
            "topology_id": self.topology_id,
            "source_id": self.source_id,
            "role": self.role,
            "relation_to_active_project": self.relation_to_active_project,
            "compatibility_status": self.compatibility_status,
            "reuse_policy": self.reuse_policy,
            "source_lean_toolchain": self.source_lean_toolchain,
            "source_mathlib_revision": self.source_mathlib_revision,
            "active_lean_toolchain": self.active_lean_toolchain,
            "active_mathlib_revision": self.active_mathlib_revision,
            "identity_basis": list(self.identity_basis),
            "evidence_status": FORMAL_SOURCE_TOPOLOGY_EVIDENCE_STATUS,
        }


@dataclass(frozen=True)
class _ConfiguredSource:
    topology: FormalSourceTopology
    entry_modules: tuple[str, ...]
    git_remotes: tuple[str, ...]
    source_root_names: tuple[str, ...]


@dataclass(frozen=True)
class _TopologyPolicy:
    topology_id: str
    active_project_source_id: str
    sources: tuple[_ConfiguredSource, ...]


def read_lean_rag_graph_metadata(db_path: Path | str) -> dict[str, str]:
    """Read graph identity metadata without trusting its filename."""

    import sqlite3
    from contextlib import closing

    path = Path(db_path).expanduser()
    if not path.exists():
        return {}
    try:
        with closing(sqlite3.connect(path)) as conn:
            has_meta = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'meta'"
            ).fetchone()
            if has_meta is None:
                return {}
            return {
                str(key): str(value)
                for key, value in conn.execute("SELECT key, value FROM meta")
            }
    except sqlite3.DatabaseError:
        return {}


def identify_formal_source_topology(
    metadata: Mapping[str, object],
) -> FormalSourceTopology | None:
    """Identify one configured source from snapshot-bound graph metadata.

    A profile is returned only when the available identity signals select one
    source unambiguously. Callers may retain a legacy path fallback for old
    fixture graphs that do not carry snapshot metadata.
    """

    policy = load_formal_source_topology_policy()
    remote = _normalize_git_remote(metadata.get("source_git_remote", ""))
    entry_module = str(metadata.get("entry_module", "") or "").strip()
    source_root_name = Path(
        str(metadata.get("source_root", "") or "").rstrip("/\\")
    ).name
    if remote:
        matches = [
            source for source in policy.sources if remote in source.git_remotes
        ]
        if len(matches) != 1:
            return None
        source = matches[0]
        if entry_module and entry_module not in source.entry_modules:
            return None
        basis = ["source_git_remote"]
    else:
        matches = [
            source
            for source in policy.sources
            if entry_module and entry_module in source.entry_modules
        ]
        if len(matches) != 1:
            return None
        source = matches[0]
        basis = ["entry_module"]
    if entry_module and entry_module in source.entry_modules:
        if "entry_module" not in basis:
            basis.append("entry_module")
    if source_root_name and source_root_name in source.source_root_names:
        basis.append("source_root_name")
    topology = source.topology
    return replace(
        topology,
        source_lean_toolchain=str(metadata.get("lean_toolchain", "") or ""),
        source_mathlib_revision=str(
            metadata.get("mathlib_revision", "") or ""
        ),
        identity_basis=tuple(basis),
    )


def resolve_formal_source_topologies(
    topologies: Sequence[FormalSourceTopology],
) -> tuple[FormalSourceTopology, ...]:
    """Bind source profiles to the active project's actual toolchain snapshot."""

    policy = load_formal_source_topology_policy()
    active_rows = [
        row for row in topologies if row.source_id == policy.active_project_source_id
    ]
    active = active_rows[0] if len(active_rows) == 1 else None
    resolved: list[FormalSourceTopology] = []
    for row in topologies:
        compatibility = "active_project"
        if not row.is_active_project:
            compatibility = _compatibility_status(row, active)
        resolved.append(
            replace(
                row,
                compatibility_status=compatibility,
                active_lean_toolchain=(
                    active.source_lean_toolchain if active is not None else ""
                ),
                active_mathlib_revision=(
                    active.source_mathlib_revision if active is not None else ""
                ),
            )
        )
    return tuple(resolved)


def fallback_formal_source_topology(source_id: str) -> FormalSourceTopology | None:
    """Return a configured profile for an explicitly inferred legacy source id."""

    requested = str(source_id or "").strip()
    for source in load_formal_source_topology_policy().sources:
        if requested in (source.topology.source_id, *source.topology.aliases):
            return source.topology
    return None


@lru_cache(maxsize=1)
def load_formal_source_topology_policy() -> _TopologyPolicy:
    raw = json.loads(FORMAL_SOURCE_TOPOLOGY_POLICY_PATH.read_text(encoding="utf-8"))
    if raw.get("schema_version") != 1:
        raise ValueError("unsupported formal source topology schema")
    topology_id = _required_text(raw, "topology_id")
    active_project_source_id = _required_text(raw, "active_project_source_id")
    raw_sources = raw.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError("formal source topology requires non-empty sources")
    sources: list[_ConfiguredSource] = []
    seen_ids: set[str] = set()
    for raw_source in raw_sources:
        if not isinstance(raw_source, dict):
            raise ValueError("formal source topology source rows must be objects")
        source_id = _required_text(raw_source, "source_id")
        if source_id in seen_ids:
            raise ValueError(f"duplicate formal source topology id: {source_id}")
        seen_ids.add(source_id)
        aliases = _text_tuple(raw_source.get("aliases", ()))
        if source_id in aliases:
            raise ValueError(f"source id repeated as alias: {source_id}")
        sources.append(
            _ConfiguredSource(
                topology=FormalSourceTopology(
                    source_id=source_id,
                    aliases=aliases,
                    role=_required_text(raw_source, "role"),
                    relation_to_active_project=_required_text(
                        raw_source, "relation_to_active_project"
                    ),
                    reuse_policy=_required_text(raw_source, "reuse_policy"),
                    topology_id=topology_id,
                    is_active_project=source_id == active_project_source_id,
                ),
                entry_modules=_text_tuple(raw_source.get("entry_modules", ())),
                git_remotes=tuple(
                    _normalize_git_remote(value)
                    for value in _text_tuple(raw_source.get("git_remotes", ()))
                ),
                source_root_names=_text_tuple(
                    raw_source.get("source_root_names", ())
                ),
            )
        )
    if active_project_source_id not in seen_ids:
        raise ValueError("active formal source is not declared")
    return _TopologyPolicy(
        topology_id=topology_id,
        active_project_source_id=active_project_source_id,
        sources=tuple(sources),
    )


def _compatibility_status(
    source: FormalSourceTopology,
    active: FormalSourceTopology | None,
) -> str:
    if active is None:
        return "active_project_snapshot_unavailable"
    source_toolchain = source.source_lean_toolchain
    active_toolchain = active.source_lean_toolchain
    source_mathlib = source.source_mathlib_revision.lower()
    active_mathlib = active.source_mathlib_revision.lower()
    if not source_toolchain or not active_toolchain:
        return "toolchain_relation_unknown"
    if source_toolchain != active_toolchain:
        return "different_lean_toolchain_requires_port"
    if not _valid_revision(source_mathlib) or not _valid_revision(active_mathlib):
        return "mathlib_relation_unknown"
    if source_mathlib != active_mathlib:
        return "different_mathlib_revision_requires_port"
    return "same_lean_toolchain_and_mathlib_revision"


def _normalize_git_remote(value: object) -> str:
    remote = str(value or "").strip().lower().replace("\\", "/")
    if remote.startswith("git@github.com:"):
        remote = "github.com/" + remote[len("git@github.com:") :]
    for prefix in ("https://", "http://", "ssh://git@"):
        if remote.startswith(prefix):
            remote = remote[len(prefix) :]
    return remote.removesuffix(".git").rstrip("/")


def _valid_revision(value: str) -> bool:
    return bool(_HEX_REVISION_RE.fullmatch(value))


def _required_text(row: Mapping[str, object], key: str) -> str:
    value = str(row.get(key, "") or "").strip()
    if not value:
        raise ValueError(f"formal source topology missing {key}")
    return value


def _text_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("formal source topology list field must be an array")
    rows = tuple(str(item).strip() for item in value if str(item).strip())
    if len(rows) != len(set(rows)):
        raise ValueError("formal source topology list field contains duplicates")
    return rows
