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
FORMAL_SOURCE_SCOPE_EXPANSION_POLICY = (
    "explicit_scope_plus_transitive_declared_dependencies_v1"
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
    dependency_source_ids: tuple[str, ...] = ()

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
            "dependency_source_ids": list(self.dependency_source_ids),
            "source_scope_expansion_policy": (
                FORMAL_SOURCE_SCOPE_EXPANSION_POLICY
            ),
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


def configured_formal_source_entry_modules(source_id: str) -> tuple[str, ...]:
    """Return canonical Lean entry modules for a configured source or alias."""

    requested = str(source_id or "").strip()
    for source in load_formal_source_topology_policy().sources:
        if requested in (source.topology.source_id, *source.topology.aliases):
            return source.entry_modules
    return ()


def canonicalize_formal_source_scope_ids(
    source_scope_ids: Sequence[str],
) -> tuple[str, ...]:
    """Resolve configured aliases while preserving unknown source identities."""

    requested = tuple(
        dict.fromkeys(
            str(value).strip()
            for value in source_scope_ids
            if str(value).strip()
        )
    )
    if not requested:
        return ()
    policy = load_formal_source_topology_policy()
    source_by_identity = {
        identity: source
        for source in policy.sources
        for identity in (
            source.topology.source_id,
            *source.topology.aliases,
        )
    }
    return tuple(
        dict.fromkeys(
            source_by_identity[source_id].topology.source_id
            if source_id in source_by_identity
            else source_id
            for source_id in requested
        )
    )


def expand_formal_source_scope_ids(
    source_scope_ids: Sequence[str],
) -> tuple[str, ...]:
    """Resolve aliases and include only dependencies declared by source policy."""

    requested = canonicalize_formal_source_scope_ids(source_scope_ids)
    if not requested:
        return ()
    policy = load_formal_source_topology_policy()
    source_by_id = {
        source.topology.source_id: source
        for source in policy.sources
    }
    effective: list[str] = []
    pending = list(requested)
    while pending:
        requested_id = pending.pop(0)
        source = source_by_id.get(requested_id)
        if requested_id in effective:
            continue
        effective.append(requested_id)
        if source is not None:
            pending.extend(source.topology.dependency_source_ids)
    return tuple(effective)


def active_project_formal_source_scope_ids(
    topology_rows: object,
) -> tuple[str, ...]:
    """Extract active source identities from retriever prompt metadata."""

    if isinstance(topology_rows, Mapping):
        topology_rows = (topology_rows,)
    if not isinstance(topology_rows, (list, tuple)):
        return ()
    return tuple(
        dict.fromkeys(
            str(row.get("source_id", "") or "").strip()
            for row in topology_rows
            if isinstance(row, Mapping)
            and (
                str(row.get("relation_to_active_project", "") or "").strip()
                == "active_project"
                or row.get("is_active_project") is True
            )
            and str(row.get("source_id", "") or "").strip()
        )
    )


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
    seen_identities: set[str] = set()
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
        identities = (source_id, *aliases)
        duplicate_identities = seen_identities.intersection(identities)
        if duplicate_identities:
            duplicate = sorted(duplicate_identities)[0]
            raise ValueError(f"duplicate formal source identity: {duplicate}")
        seen_identities.update(identities)
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
                    dependency_source_ids=_text_tuple(
                        raw_source.get("dependency_source_ids", ())
                    ),
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
    _validate_source_dependencies(sources)
    return _TopologyPolicy(
        topology_id=topology_id,
        active_project_source_id=active_project_source_id,
        sources=tuple(sources),
    )


def _validate_source_dependencies(sources: Sequence[_ConfiguredSource]) -> None:
    source_ids = {source.topology.source_id for source in sources}
    dependencies = {
        source.topology.source_id: source.topology.dependency_source_ids
        for source in sources
    }
    for source_id, dependency_ids in dependencies.items():
        for dependency_id in dependency_ids:
            if dependency_id not in source_ids:
                raise ValueError(
                    f"unknown formal source dependency: {source_id} -> {dependency_id}"
                )
            if dependency_id == source_id:
                raise ValueError(f"self-dependent formal source: {source_id}")

    visited: set[str] = set()
    active: set[str] = set()

    def visit(source_id: str) -> None:
        if source_id in active:
            raise ValueError("cyclic formal source dependencies")
        if source_id in visited:
            return
        active.add(source_id)
        for dependency_id in dependencies[source_id]:
            visit(dependency_id)
        active.remove(source_id)
        visited.add(source_id)

    for source_id in sorted(source_ids):
        visit(source_id)


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
