from __future__ import annotations

import base64
import gzip
import hashlib
import html
import io
import json
import re
import tarfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Protocol, Sequence

from .fingerprint import stable_hash
from .model_backend import ClientToolDefinition
from .research_source_library import ResearchSourceSnapshot, load_research_source_snapshot
from .research_source_project import acquire_public_github_repository_snapshot
from .storage.public_source_observations import (
    PublicSourceObservationStore,
    ResearchSourceDiscoveryError,
)


RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL = "discover_research_sources"
RESEARCH_SOURCE_DISCOVERY_READ_TOOL = "read_discovered_research_source"
RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL = "acquire_discovered_research_repository"
RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE = (
    "PUBLIC_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE"
)
MAX_DISCOVERY_RESULTS = 10
MAX_DISCOVERY_QUERY_CHARS = 500
MAX_DISCOVERY_API_BYTES = 2_000_000
MAX_DISCOVERY_HTML_BYTES = 5_000_000
MAX_DISCOVERY_TEXT_BYTES = 250_000
MAX_DISCOVERY_OBSERVATION_CHARS = 50_000
GITHUB_API_VERSION = "2022-11-28"
ARXIV_MIN_REQUEST_INTERVAL_SECONDS = 3.0
PUBLIC_DISCOVERY_HOSTS = frozenset(
    {
        "api.crossref.org",
        "api.github.com",
        "arxiv.org",
        "export.arxiv.org",
    }
)
ARXIV_ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
ARXIV_IDENTIFIER_PATTERN = re.compile(
    r"(?:[0-9]{4}\.[0-9]{4,5}|[A-Za-z.-]+/[0-9]{7})v[1-9][0-9]*"
)


class ResearchSourceDiscoveryInputError(ValueError):
    """A model-actionable public-source tool input error."""


JSONFetcher = Callable[[str, Mapping[str, str], float], Any]
BytesFetcher = Callable[[str, Mapping[str, str], float, int], bytes]
RequestPacer = Callable[[], None]


class _ArxivRequestPacer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_request_started = 0.0

    def __call__(self) -> None:
        with self._lock:
            now = time.monotonic()
            remaining = (
                self._last_request_started
                + ARXIV_MIN_REQUEST_INTERVAL_SECONDS
                - now
            )
            if remaining > 0:
                time.sleep(remaining)
            self._last_request_started = time.monotonic()


_DEFAULT_ARXIV_REQUEST_PACER = _ArxivRequestPacer()


class ResearchSourceDiscovery(Protocol):
    provider_name: str

    def descriptor(self) -> Mapping[str, Any]: ...

    def search(
        self,
        query: str,
        *,
        source_kind: str = "all",
        top_k: int = 5,
    ) -> Mapping[str, Any]: ...

    def read(
        self,
        source_handle: str,
        *,
        path: str = "",
        revision: str = "",
        line_start: int = 0,
        line_end: int = 0,
    ) -> Mapping[str, Any]: ...

    def acquire_repository(
        self, source_handle: str, *, revision: str
    ) -> Mapping[str, Any]: ...


def research_source_discovery_client_tools(
    *, repository_acquisition: bool = False,
) -> tuple[ClientToolDefinition, ...]:
    search_schema = {
        "type": "object", "additionalProperties": False, "required": ["query"],
        "properties": {
            "query": {"type": "string", "minLength": 1, "maxLength": MAX_DISCOVERY_QUERY_CHARS},
            "source_kind": {"type": "string", "enum": ["all", "paper", "preprint", "repository"]},
            "top_k": {"type": "integer", "minimum": 1, "maximum": MAX_DISCOVERY_RESULTS},
        },
    }
    read_schema = {
        "type": "object", "additionalProperties": False,
        "required": ["source_handle"],
        "properties": {
            "source_handle": {"type": "string", "minLength": 1},
            "path": {"type": "string"}, "revision": {"type": "string"},
            "line_start": {"type": "integer", "minimum": 1},
            "line_end": {"type": "integer", "minimum": 1},
        },
    }
    tools = (
        ClientToolDefinition(
            name=RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL,
            description=(
                "Search public scholarly metadata, arXiv preprints, and GitHub repositories "
                "under the configured horizon; choose the query and inspect opaque handles."
            ),
            input_schema=search_schema,
        ),
        ClientToolDefinition(
            name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
            description=(
                "Read bounded metadata, pinned arXiv HTML or original source, and "
                "pinned repository text. For a preprint use an empty path for HTML, "
                "source for its archive listing, or source/<listed path> for exact text. "
                "Resolve a repository revision/root first, then navigate or read ranges."
            ),
            input_schema=read_schema,
        ),
    )
    if repository_acquisition:
        tools += (ClientToolDefinition(
            name=RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL,
            description=(
                "Acquire the complete public Git repository at a previously resolved "
                "commit into immutable local source storage. Subsequent source reads "
                "and scientific file imports use these exact bytes without network. "
                "This does not install dependencies, run code, or establish replication."
            ),
            input_schema={
                "type": "object", "additionalProperties": False,
                "required": ["source_handle", "revision"],
                "properties": {
                    "source_handle": {"type": "string", "minLength": 1},
                    "revision": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                },
            },
        ),)
    return tools


def execute_research_source_discovery_client_tool(
    discovery: ResearchSourceDiscovery,
    *,
    tool_name: str,
    tool_input: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    """Execute one shared discovery tool and return a compact provenance ref."""

    is_search = tool_name == RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL
    is_acquisition = tool_name == RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL
    if not is_search and not is_acquisition and tool_name != RESEARCH_SOURCE_DISCOVERY_READ_TOOL:
        raise ResearchSourceDiscoveryInputError("unsupported public research source discovery tool")
    allowed = ({"query", "source_kind", "top_k"} if is_search else
               {"source_handle", "revision"} if is_acquisition else
               {"source_handle", "path", "revision", "line_start", "line_end"})
    if set(tool_input) - allowed:
        accepted = ", ".join(sorted(allowed))
        raise ResearchSourceDiscoveryInputError(f"{tool_name} accepts only {accepted}")
    try:
        if is_search:
            observation = discovery.search(
                tool_input.get("query", ""),
                source_kind=tool_input.get("source_kind", "all"),
                top_k=tool_input.get("top_k", 5),
            )
        elif is_acquisition:
            observation = discovery.acquire_repository(
                tool_input.get("source_handle", ""), revision=tool_input.get("revision", "")
            )
        else:
            read_kwargs = {"path": tool_input.get("path", ""), "revision": tool_input.get("revision", "")}
            if "line_start" in tool_input or "line_end" in tool_input:
                read_kwargs.update(
                    line_start=tool_input.get("line_start", 0),
                    line_end=tool_input.get("line_end", 0),
                )
            observation = discovery.read(tool_input.get("source_handle", ""), **read_kwargs)
    except ResearchSourceDiscoveryError as exc:
        return {
            "ok": False, "error": "public_research_source_discovery_failed",
            "detail": str(exc),
            "model_may_continue_without_this_source": True,
        }, {}, True
    if not isinstance(observation, Mapping):
        raise RuntimeError("research source discovery returned a non-object observation")

    compact = dict(observation)
    ref_fields = (
        ("provider", "source_horizon", "query_hash", "source_kind") if is_search else
        ("provider", "source_handle", "source_kind", "revision", "snapshot") if is_acquisition else
        ("provider", "source_handle", "source_kind", "title", "url", "publication_date",
         "revision", "path", "content_sha256", "content_line_count", "content_truncated",
         "line_start", "line_end",
         "content_range_sha256", "citation_ref")
    )
    source_ref = {"tool": tool_name, **{key: compact.get(key, "") for key in ref_fields}}
    if is_search:
        result_fields = ("source_handle", "source_kind", "title", "url", "publication_date")
        source_ref["results"] = [
            {key: row[key] for key in result_fields if key in row}
            for row in compact.get("results", []) if isinstance(row, Mapping)]
    source_ref["proof_evidence_status"] = RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
    return compact, source_ref, False

@dataclass(frozen=True)
class PublicResearchSourceDiscoveryConfig:
    source_horizon: str
    contact_email: str = ""
    timeout_seconds: float = 20.0

    def __post_init__(self) -> None:
        try:
            date.fromisoformat(self.source_horizon)
        except ValueError as exc:
            raise ValueError(
                "research source horizon must be an ISO date (YYYY-MM-DD)"
            ) from exc
        if self.timeout_seconds <= 0:
            raise ValueError("research source discovery timeout must be positive")
        if self.contact_email and not re.fullmatch(
            r"[^\s@]+@[^\s@]+\.[^\s@]+", self.contact_email
        ):
            raise ValueError("research source contact email is invalid")


class PublicResearchSourceDiscovery:
    """Model-directed paper/preprint/repository lookup over fixed public hosts.

    This is a thin tool provider, not a literature agent. The caller's model owns
    every query and source selection. Strict historical or hidden-answer benchmarks
    should continue to use operator-frozen ``ResearchSourceSnapshot`` inputs.
    """

    provider_name = "crossref_arxiv_github_public_api"

    def __init__(
        self,
        *,
        config: PublicResearchSourceDiscoveryConfig,
        github_token: str = "",
        state_dir: Path | None = None,
        json_fetcher: JSONFetcher | None = None,
        bytes_fetcher: BytesFetcher | None = None,
        arxiv_request_pacer: RequestPacer | None = None,
    ) -> None:
        self.config = config
        self._github_token = str(github_token or "").strip()
        self._json_fetcher = json_fetcher or _fetch_json
        self._bytes_fetcher = bytes_fetcher or _fetch_text
        self._arxiv_request_pacer = (
            arxiv_request_pacer or _DEFAULT_ARXIV_REQUEST_PACER
        )
        self._state_dir = state_dir.resolve() if state_dir is not None else None
        self._repository_snapshots: dict[tuple[str, str], ResearchSourceSnapshot] = {}
        self._observations = PublicSourceObservationStore(
            state_dir=self._state_dir,
            provider=self.provider_name,
            source_horizon=self.config.source_horizon,
            max_content_bytes=MAX_DISCOVERY_HTML_BYTES,
            proof_evidence_status=RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE,
        )

    def descriptor(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "artifact_kind": "PublicResearchSourceDiscoveryDescriptor",
            "provider": self.provider_name,
            "source_horizon": self.config.source_horizon,
            "source_kinds": ["paper", "preprint", "repository"],
            "api_hosts": sorted(PUBLIC_DISCOVERY_HOSTS),
            "model_selects_queries": True,
            "model_selects_sources": True,
            "arbitrary_url_fetch_allowed": False,
            "author_source_execution_allowed": False,
            "repository_snapshot_acquisition_allowed": self._state_dir is not None,
            "strict_historical_benchmark_authority": False,
            "durable_exact_observation_store": self._state_dir is not None,
            "durable_observation_policy": "hash_bound_exact_model_observations_v1"
            if self._state_dir is not None else "in_memory_session_only",
            "secret_values_model_visible": False,
            "proof_evidence_status": (
                RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
            ),
            "boundary": (
                "Live public API observations can ground literature and repository "
                "scouting. Exact-version arXiv HTML/source is preprint text, not publication "
                "authority. These observations are not a frozen benchmark corpus, "
                "independent review, replication evidence, or mathematical proof."
            ),
        }

    def new_session(self) -> PublicResearchSourceDiscovery:
        """Return an isolated provider object over the same durable observations."""

        return PublicResearchSourceDiscovery(
            config=self.config,
            github_token=self._github_token,
            state_dir=self._state_dir,
            json_fetcher=self._json_fetcher,
            bytes_fetcher=self._bytes_fetcher,
            arxiv_request_pacer=self._arxiv_request_pacer,
        )

    def search(
        self,
        query: str,
        *,
        source_kind: str = "all",
        top_k: int = 5,
    ) -> dict[str, Any]:
        normalized_query = str(query or "").strip()
        normalized_kind = str(source_kind or "all").strip().lower()
        if not normalized_query:
            raise ResearchSourceDiscoveryInputError(
                "research source discovery query must be nonempty"
            )
        if len(normalized_query) > MAX_DISCOVERY_QUERY_CHARS:
            raise ResearchSourceDiscoveryInputError(
                f"research source discovery query exceeds {MAX_DISCOVERY_QUERY_CHARS} characters"
            )
        if normalized_kind not in {"all", "paper", "preprint", "repository"}:
            raise ResearchSourceDiscoveryInputError(
                "research source kind must be all, paper, preprint, or repository"
            )
        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise ResearchSourceDiscoveryInputError(
                "research source discovery top_k must be an integer"
            )
        if top_k < 1 or top_k > MAX_DISCOVERY_RESULTS:
            raise ResearchSourceDiscoveryInputError(
                f"research source discovery top_k must be between 1 and {MAX_DISCOVERY_RESULTS}"
            )

        paper_rows = (
            self._search_crossref(normalized_query, top_k=top_k)
            if normalized_kind in {"all", "paper"}
            else []
        )
        preprint_rows = (
            self._search_arxiv(normalized_query, top_k=top_k)
            if normalized_kind in {"all", "preprint"}
            else []
        )
        repository_rows = (
            self._search_github(normalized_query, top_k=top_k)
            if normalized_kind in {"all", "repository"}
            else []
        )
        if normalized_kind == "all":
            rows = _round_robin_rows(
                (paper_rows, preprint_rows, repository_rows),
                limit=top_k,
            )
        else:
            rows = (paper_rows or preprint_rows or repository_rows)[:top_k]
        rows = self._observations.pin_results(rows)
        return {
            "ok": True,
            "provider": self.provider_name,
            "source_horizon": self.config.source_horizon,
            "query": normalized_query,
            "query_hash": stable_hash(normalized_query),
            "source_kind": normalized_kind,
            "results": [_public_search_result(row) for row in rows],
            "proof_evidence_status": (
                RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
            ),
            "boundary": (
                "The model chose this query and must inspect any useful result. Search "
                "ranking, metadata, and preprint hosting do not establish a scientific "
                "claim or publication status."
            ),
        }

    def read(
        self,
        source_handle: str,
        *,
        path: str = "",
        revision: str = "",
        line_start: int = 0,
        line_end: int = 0,
    ) -> dict[str, Any]:
        normalized_handle = str(source_handle or "").strip()
        row = self._observations.result(normalized_handle)
        if row is None:
            raise ResearchSourceDiscoveryInputError(
                "discovered source handle is unknown in this model session; search first"
            )
        if row["source_kind"] == "paper":
            if str(path or "").strip() or str(revision or "").strip():
                raise ResearchSourceDiscoveryInputError(
                    "paper discovery reads do not accept path or revision"
                )
            stored = self._read_crossref(row)
        elif row["source_kind"] == "preprint":
            if str(revision or "").strip():
                raise ResearchSourceDiscoveryInputError(
                    "preprint discovery reads do not accept revision; the discovered version is pinned"
                )
            selected_path = str(path or "").strip()
            if selected_path and selected_path != "source" and not selected_path.startswith("source/"):
                raise ResearchSourceDiscoveryInputError("preprint reads do not accept path except source or source/<listed path>")
            stored = (self._read_arxiv_source(row, _normalized_repository_path(selected_path))
                      if selected_path else self._read_arxiv(row))
        else:
            stored = self._read_github(row, path=str(path or "").strip(), revision=str(revision or "").strip())
        return _source_read_observation(
            **stored, line_start=line_start, line_end=line_end
        )

    def acquire_repository(self, source_handle: str, *, revision: str) -> dict[str, Any]:
        row = self._observations.result(str(source_handle or "").strip())
        if row is None or row.get("source_kind") != "repository":
            raise ResearchSourceDiscoveryInputError("acquisition requires a discovered repository handle")
        if self._state_dir is None:
            raise ResearchSourceDiscoveryInputError("repository acquisition requires durable source storage")
        handle = str(row["source_handle"])
        if not isinstance(revision, str) or revision not in self._observations.revisions(handle):
            raise ResearchSourceDiscoveryInputError("repository acquisition requires a previously resolved revision")
        snapshot = self._acquired_repository(row, revision)
        if snapshot is None:
            try:
                snapshot = acquire_public_github_repository_snapshot(
                    repository_url=f"https://github.com/{row['repository']}",
                    revision=revision,
                    output_dir=self._repository_directory(handle, revision),
                    snapshot_id="public-repository:" + stable_hash([handle, revision]),
                    source_horizon=self.config.source_horizon,
                )
            except (OSError, ValueError) as exc:
                raise ResearchSourceDiscoveryError(str(exc)) from exc
            self._observations.pin_snapshot(handle, revision, snapshot.descriptor())
            self._repository_snapshots[(handle, revision)] = snapshot
        errors = snapshot.identity_errors()
        if errors:
            raise ResearchSourceDiscoveryError("acquired repository is unavailable: " + "; ".join(errors))
        return {
            "ok": True, "provider": self.provider_name,
            "source_handle": handle, "source_kind": "repository", "revision": revision,
            "snapshot": snapshot.descriptor(),
            "proof_evidence_status": RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE,
        }

    def _repository_directory(self, source_handle: str, revision: str) -> Path:
        assert self._state_dir is not None
        return self._state_dir / "repositories" / stable_hash([source_handle, revision])

    def acquired_repository_snapshot(self, source_handle: str, revision: str) -> ResearchSourceSnapshot:
        """Resolve already acquired bytes without fetching or selecting a revision."""
        row = self._observations.result(source_handle)
        if (row is None or row.get("source_kind") != "repository"
            or revision not in self._observations.revisions(source_handle)):
            raise ResearchSourceDiscoveryInputError("execution requires an observed repository and revision")
        snapshot = self._acquired_repository(row, revision)
        if snapshot is None:
            raise ResearchSourceDiscoveryInputError("acquire this exact repository revision before executing it")
        return snapshot

    def _acquired_repository(
        self, row: Mapping[str, Any], revision: str
    ) -> ResearchSourceSnapshot | None:
        handle = str(row["source_handle"])
        expected = self._observations.snapshot(handle, revision)
        if expected is None:
            return None
        manifest_path = self._repository_directory(handle, revision) / "sources.json"
        try:
            manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        except OSError as exc:
            raise ResearchSourceDiscoveryError(f"acquired repository is unavailable: {exc}") from exc
        if manifest_hash != expected.get("manifest_sha256"):
            raise ResearchSourceDiscoveryError("acquired repository snapshot identity changed")
        snapshot = self._repository_snapshots.get((handle, revision))
        if snapshot is None:
            try:
                snapshot = load_research_source_snapshot(manifest_path)
            except (OSError, ValueError) as exc:
                raise ResearchSourceDiscoveryError(f"acquired repository is unavailable: {exc}") from exc
            if snapshot.descriptor() != expected:
                raise ResearchSourceDiscoveryError("acquired repository snapshot identity changed")
        self._repository_snapshots[(handle, revision)] = snapshot
        return snapshot

    def _search_crossref(self, query: str, *, top_k: int) -> list[dict[str, Any]]:
        params = {
            "query.bibliographic": query,
            "filter": f"until-pub-date:{self.config.source_horizon}",
            "rows": str(top_k),
        }
        if self.config.contact_email:
            params["mailto"] = self.config.contact_email
        payload = self._json_fetcher(
            "https://api.crossref.org/works?" + urllib.parse.urlencode(params),
            self._crossref_headers(),
            self.config.timeout_seconds,
        )
        items = (
            payload.get("message", {}).get("items", [])
            if isinstance(payload, Mapping)
            and isinstance(payload.get("message"), Mapping)
            else []
        )
        rows: list[dict[str, Any]] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, Mapping):
                continue
            doi = str(item.get("DOI", "") or "").strip().lower()
            title = _first_text(item.get("title"))
            publication_date = _crossref_publication_date(item)
            if (
                not doi
                or not title
                or (
                    publication_date
                    and publication_date > self.config.source_horizon
                )
            ):
                continue
            identity = f"doi:{doi}"
            rows.append(
                {
                    "source_handle": _source_handle(
                        self.provider_name,
                        "paper",
                        identity,
                        self.config.source_horizon,
                    ),
                    "source_kind": "paper",
                    "source_identity": identity,
                    "doi": doi,
                    "title": title,
                    "url": str(item.get("URL", "") or f"https://doi.org/{doi}"),
                    "publication_date": publication_date,
                    "citation": _crossref_citation(item),
                    "summary": _clean_markup(str(item.get("abstract", "") or ""))[
                        :1_500
                    ],
                }
            )
        return rows

    def _search_arxiv(self, query: str, *, top_k: int) -> list[dict[str, Any]]:
        horizon_stamp = self.config.source_horizon.replace("-", "") + "2359"
        search_terms = re.findall(
            r"[\w]+(?:[.-][\w]+)*",
            str(query or ""),
            flags=re.UNICODE,
        )
        if not search_terms:
            raise ResearchSourceDiscoveryInputError(
                "preprint discovery query must contain a searchable term"
            )
        search_clause = " AND ".join(
            f'all:"{term}"' for term in search_terms
        )
        params = {
            "search_query": (
                search_clause
                + " AND "
                f"submittedDate:[199101010000 TO {horizon_stamp}]"
            ),
            "start": "0",
            "max_results": str(top_k),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        self._arxiv_request_pacer()
        raw = self._bytes_fetcher(
            "https://export.arxiv.org/api/query?"
            + urllib.parse.urlencode(params),
            self._arxiv_headers(),
            self.config.timeout_seconds,
            MAX_DISCOVERY_API_BYTES,
        )
        rows: list[dict[str, Any]] = []
        for item in _arxiv_atom_rows(raw):
            publication_date = str(item["published"])
            updated_date = str(item["updated"])
            if (
                publication_date > self.config.source_horizon
                or updated_date > self.config.source_horizon
            ):
                continue
            arxiv_id = str(item["arxiv_id"])
            identity = f"arxiv:{arxiv_id.lower()}"
            rows.append(
                {
                    "source_handle": _source_handle(
                        self.provider_name,
                        "preprint",
                        identity,
                        self.config.source_horizon,
                    ),
                    "source_kind": "preprint",
                    "source_identity": identity,
                    "arxiv_id": arxiv_id,
                    "title": str(item["title"]),
                    "url": f"https://arxiv.org/html/{arxiv_id}",
                    "publication_date": publication_date,
                    "updated_date": updated_date,
                    "citation": _arxiv_citation(item),
                    "summary": str(item["summary"])[:1_500],
                }
            )
        return rows

    def _search_github(self, query: str, *, top_k: int) -> list[dict[str, Any]]:
        params = {
            "q": f"{query} created:<={self.config.source_horizon}",
            "per_page": str(top_k),
        }
        payload = self._json_fetcher(
            "https://api.github.com/search/repositories?"
            + urllib.parse.urlencode(params),
            self._github_headers(),
            self.config.timeout_seconds,
        )
        items = payload.get("items", []) if isinstance(payload, Mapping) else []
        rows: list[dict[str, Any]] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, Mapping):
                continue
            full_name = str(item.get("full_name", "") or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", full_name):
                continue
            identity = f"github:{full_name.lower()}"
            rows.append(
                {
                    "source_handle": _source_handle(
                        self.provider_name,
                        "repository",
                        identity,
                        self.config.source_horizon,
                    ),
                    "source_kind": "repository",
                    "source_identity": identity,
                    "repository": full_name,
                    "default_branch": str(
                        item.get("default_branch", "") or ""
                    ).strip(),
                    "title": full_name,
                    "url": str(
                        item.get("html_url", "")
                        or f"https://github.com/{full_name}"
                    ),
                    "publication_date": str(item.get("created_at", "") or "")[:10],
                    "citation": f"GitHub repository {full_name}",
                    "summary": str(item.get("description", "") or "")[:1_500],
                }
            )
        return rows

    def _remember_source(self, row: Mapping[str, Any], **metadata: Any) -> dict[str, Any]:
        fields = ("source_handle", "source_kind", "source_identity", "title", "url", "publication_date", "citation")
        return self._observations.remember_read({
            "provider": self.provider_name,
            **{key: str(row.get(key, "") or "") for key in fields}, **metadata,
        })

    def _read_crossref(self, row: Mapping[str, Any]) -> Mapping[str, Any]:
        stored = self._observations.read_for_path(str(row["source_handle"]), "metadata.md")
        if stored is not None:
            return stored
        doi = str(row["doi"])
        payload = self._json_fetcher(
            "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe=""),
            self._crossref_headers(),
            self.config.timeout_seconds,
        )
        item = payload.get("message", {}) if isinstance(payload, Mapping) else {}
        if not isinstance(item, Mapping):
            raise ResearchSourceDiscoveryError(
                "Crossref returned an invalid work record"
            )
        publication_date = _crossref_publication_date(item)
        if publication_date and publication_date > self.config.source_horizon:
            raise ResearchSourceDiscoveryError(
                "Crossref work falls after the configured source horizon"
            )
        return self._remember_source(
            row, title=_first_text(item.get("title")) or str(row["title"]),
            url=str(item.get("URL", "") or row["url"]), publication_date=publication_date,
            citation=_crossref_citation(item) or str(row["citation"]),
            revision="crossref-record:" + stable_hash(item)[:24], path="metadata.md",
            content=_crossref_markdown(item, fallback_doi=doi),
        )

    def _read_arxiv(self, row: Mapping[str, Any]) -> Mapping[str, Any]:
        arxiv_id = str(row["arxiv_id"])
        stored = self._observations.read(
            str(row["source_handle"]), arxiv_id, "paper.html"
        )
        if stored is not None:
            return stored
        url = "https://arxiv.org/html/" + urllib.parse.quote(arxiv_id, safe="/.")
        self._arxiv_request_pacer()
        raw = self._bytes_fetcher(
            url,
            self._arxiv_headers(),
            self.config.timeout_seconds,
            MAX_DISCOVERY_HTML_BYTES,
        )
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ResearchSourceDiscoveryError("arXiv HTML is not UTF-8 text") from exc
        if not re.search(r"<html(?:\s|>)", content, flags=re.IGNORECASE):
            raise ResearchSourceDiscoveryError(
                "arXiv returned a non-HTML paper representation"
            )
        return self._remember_source(row, url=url, revision=arxiv_id, path="paper.html", content=content)

    def _read_arxiv_source(self, row: Mapping[str, Any], path: str) -> Mapping[str, Any]:
        handle, version = str(row["source_handle"]), str(row["arxiv_id"])
        if self._observations.read(handle, version, "source") is None:
            url = "https://arxiv.org/src/" + urllib.parse.quote(version, safe="/.")
            self._arxiv_request_pacer()
            raw = self._bytes_fetcher(url, self._arxiv_headers(), self.config.timeout_seconds, MAX_DISCOVERY_HTML_BYTES)
            files = _arxiv_source_files(raw)
            listing = [f"# Original source: {version}", f"Archive SHA-256: {hashlib.sha256(raw).hexdigest()}"]
            for name, body in sorted(files.items()):
                try:
                    content = body.decode("utf-8")
                except UnicodeDecodeError:
                    content = None
                readable = content is not None and len(body) <= MAX_DISCOVERY_TEXT_BYTES and b"\x00" not in body
                listing.append(f"- source/{name}: {len(body)} bytes; sha256={hashlib.sha256(body).hexdigest()}; readable={readable}")
                if readable:
                    self._remember_source(row, url=url, revision=version, path="source/" + name, content=content)
            self._remember_source(row, url=url, revision=version, path="source", content="\n".join(listing) + "\n")
        stored = self._observations.read(handle, version, path)
        if stored is None:
            raise ResearchSourceDiscoveryInputError("selected arXiv source path is absent or not bounded UTF-8 text; read source for the exact listing")
        return stored

    def _read_github(
        self,
        row: Mapping[str, Any],
        *,
        path: str,
        revision: str,
    ) -> Mapping[str, Any]:
        repository = str(row["repository"])
        normalized_path = _normalized_repository_path(path)
        source_handle = str(row["source_handle"])
        allowed_revisions = self._observations.revisions(source_handle)
        if revision:
            if revision not in allowed_revisions:
                raise ResearchSourceDiscoveryInputError(
                    "GitHub revision was not resolved for this source in the current session"
                )
            resolved_revision = revision
        else:
            if len(allowed_revisions) > 1:
                raise ResearchSourceDiscoveryError(
                    "durable GitHub source has ambiguous horizon revisions"
                )
            resolved_revision = (
                next(iter(allowed_revisions))
                if allowed_revisions
                else self._github_revision_at_horizon(repository)
            )

        snapshot = self._acquired_repository(row, resolved_revision)
        acquired_content, is_directory = (
            _acquired_repository_content(snapshot, normalized_path)
            if snapshot is not None else (None, False)
        )
        stored = self._observations.read(
            source_handle, resolved_revision, normalized_path or "."
        )
        if stored is not None:
            if snapshot is not None and not is_directory and acquired_content != stored["content"]:
                raise ResearchSourceDiscoveryError("acquired repository differs from the observed source bytes")
            return stored

        quoted_repo = "/".join(
            urllib.parse.quote(part, safe="") for part in repository.split("/")
        )
        if snapshot is not None:
            content = acquired_content
            if is_directory:
                content = _github_directory_markdown(
                    repository, resolved_revision, normalized_path, content,
                    description=str(row.get("summary", "") or ""),
                )
            pinned_url = f"https://github.com/{repository}/{'tree' if is_directory else 'blob'}/{resolved_revision}"
            if normalized_path:
                pinned_url += "/" + urllib.parse.quote(normalized_path, safe="/")
        elif normalized_path:
            quoted_path = urllib.parse.quote(normalized_path, safe="/")
            payload = self._json_fetcher(
                f"https://api.github.com/repos/{quoted_repo}/contents/{quoted_path}?"
                + urllib.parse.urlencode({"ref": resolved_revision}),
                self._github_headers(),
                self.config.timeout_seconds,
            )
            if isinstance(payload, list):
                content = _github_directory_markdown(
                    repository,
                    resolved_revision,
                    normalized_path,
                    payload,
                )
                pinned_url = (
                    f"https://github.com/{repository}/tree/{resolved_revision}/"
                    f"{urllib.parse.quote(normalized_path, safe='/')}"
                )
            elif isinstance(payload, Mapping) and payload.get("encoding") == "base64":
                encoded_content = re.sub(
                    r"\s+", "", str(payload.get("content", "") or "")
                )
                try:
                    raw_content = base64.b64decode(encoded_content, validate=True)
                    content = raw_content.decode("utf-8")
                except (ValueError, UnicodeDecodeError) as exc:
                    raise ResearchSourceDiscoveryInputError(
                        "selected repository file is not UTF-8 text"
                    ) from exc
                if len(raw_content) > MAX_DISCOVERY_TEXT_BYTES:
                    raise ResearchSourceDiscoveryInputError(
                        f"selected repository file exceeds {MAX_DISCOVERY_TEXT_BYTES} bytes"
                    )
                pinned_url = (
                    f"https://github.com/{repository}/blob/{resolved_revision}/"
                    f"{urllib.parse.quote(normalized_path, safe='/')}"
                )
            else:
                raise ResearchSourceDiscoveryInputError(
                    "selected repository path is neither a directory listing nor an "
                    "inline UTF-8 file"
                )
        else:
            listing = self._json_fetcher(
                f"https://api.github.com/repos/{quoted_repo}/contents?"
                + urllib.parse.urlencode({"ref": resolved_revision}),
                self._github_headers(),
                self.config.timeout_seconds,
            )
            content = _github_directory_markdown(
                repository,
                resolved_revision,
                "",
                listing if isinstance(listing, list) else [],
                description=str(row.get("summary", "") or ""),
            )
            pinned_url = f"https://github.com/{repository}/tree/{resolved_revision}"
        return self._remember_source(
            row, url=pinned_url, citation=f"{row['citation']} at commit {resolved_revision}",
            revision=resolved_revision, path=normalized_path or ".", content=content,
        )

    def _github_revision_at_horizon(self, repository: str) -> str:
        quoted_repo = "/".join(
            urllib.parse.quote(part, safe="") for part in repository.split("/")
        )
        params = {
            "until": self.config.source_horizon + "T23:59:59Z",
            "per_page": "1",
        }
        payload = self._json_fetcher(
            f"https://api.github.com/repos/{quoted_repo}/commits?"
            + urllib.parse.urlencode(params),
            self._github_headers(),
            self.config.timeout_seconds,
        )
        rows = payload if isinstance(payload, list) else []
        revision = (
            str(rows[0].get("sha", "") or "").strip()
            if rows and isinstance(rows[0], Mapping)
            else ""
        )
        if not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
            raise ResearchSourceDiscoveryError(
                "GitHub repository has no resolvable commit at the source horizon"
            )
        return revision.lower()

    def _paper_headers(self) -> dict[str, str]:
        email = self.config.contact_email
        contact = f"; mailto:{email}" if email else ""
        agent = "AI-Statistician/0.1 (https://github.com/ykzeng-yale/AI-Statistician"
        return {"User-Agent": agent + contact + ")"}

    _crossref_headers = _paper_headers
    _arxiv_headers = _paper_headers

    def _github_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "ykzeng-yale-AI-Statistician",
        }
        if self._github_token:
            headers["Authorization"] = "Bearer " + self._github_token
        return headers


def _arxiv_source_files(raw: bytes) -> dict[str, bytes]:
    if len(raw) > MAX_DISCOVERY_HTML_BYTES:
        raise ResearchSourceDiscoveryError("arXiv source exceeds the download byte limit")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            payload = stream.read(MAX_DISCOVERY_HTML_BYTES + 1)
    except (OSError, EOFError) as exc:
        raise ResearchSourceDiscoveryError("arXiv source is not a valid gzip representation") from exc
    if not payload or len(payload) > MAX_DISCOVERY_HTML_BYTES:
        raise ResearchSourceDiscoveryError("arXiv source is empty or exceeds the expanded byte limit")
    try:
        archive = tarfile.open(fileobj=io.BytesIO(payload), mode="r:")
    except tarfile.ReadError:
        if payload.startswith(b"%PDF-"):
            raise ResearchSourceDiscoveryError("arXiv source is a PDF, not original text")
        return {"document.txt": payload}
    files: dict[str, bytes] = {}
    remaining = MAX_DISCOVERY_HTML_BYTES
    try:
        with archive:
            for member in archive:
                if member.isdir():
                    continue
                path = PurePosixPath(member.name)
                if (not member.isfile() or path.is_absolute() or ".." in path.parts
                        or not path.parts or len(str(path)) > 1_000 or str(path) in files
                        or not 0 <= member.size <= remaining):
                    raise ResearchSourceDiscoveryError("arXiv source has an unsafe, nonregular, duplicate or oversized member")
                remaining -= member.size
                with archive.extractfile(member) as stream:
                    files[str(path)] = stream.read()
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise ResearchSourceDiscoveryError("arXiv source archive is malformed") from exc
    if not files:
        raise ResearchSourceDiscoveryError("arXiv source archive contains no files")
    return files


def _fetch_json(url: str, headers: Mapping[str, str], timeout: float) -> Any:
    raw = _fetch_text(url, headers, timeout, MAX_DISCOVERY_API_BYTES)
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchSourceDiscoveryError(
            "public research API returned invalid JSON"
        ) from exc


def _fetch_text(
    url: str,
    headers: Mapping[str, str],
    timeout: float,
    max_bytes: int,
) -> bytes:
    request = urllib.request.Request(url, headers=dict(headers), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            original_host = urllib.parse.urlparse(url).hostname
            final_host = urllib.parse.urlparse(response.geturl()).hostname
            if original_host not in PUBLIC_DISCOVERY_HOSTS:
                raise ResearchSourceDiscoveryError(
                    "public research API host is not allowed"
                )
            if final_host != original_host:
                raise ResearchSourceDiscoveryError(
                    "public research API redirected outside its fixed host"
                )
            raw = response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        raise ResearchSourceDiscoveryError(
            f"public research API returned HTTP {exc.code}"
        ) from exc
    except (OSError, urllib.error.URLError) as exc:
        raise ResearchSourceDiscoveryError(
            "public research API request failed"
        ) from exc
    if len(raw) > max_bytes:
        raise ResearchSourceDiscoveryError(
            f"public research source exceeded {max_bytes} bytes"
        )
    return raw


def _source_handle(
    provider: str,
    source_kind: str,
    identity: str,
    horizon: str,
) -> str:
    return "public-source:" + stable_hash(
        [provider, source_kind, identity, horizon]
    )[:28]


def _public_search_result(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "source_handle",
            "source_kind",
            "title",
            "url",
            "publication_date",
            "citation",
            "summary",
        )
        if key in row
    }


def _source_read_observation(
    *,
    provider: str,
    source_handle: str,
    source_kind: str,
    source_identity: str,
    title: str,
    url: str,
    publication_date: str,
    citation: str,
    revision: str,
    path: str,
    content: str,
    line_start: int = 0,
    line_end: int = 0,
) -> dict[str, Any]:
    lines = content.splitlines()
    range_requested = line_start != 0 or line_end != 0
    if range_requested:
        if (
            isinstance(line_start, bool)
            or not isinstance(line_start, int)
            or isinstance(line_end, bool)
            or not isinstance(line_end, int)
            or line_start < 1
            or line_end < line_start
            or line_end > len(lines)
        ):
            raise ResearchSourceDiscoveryInputError(
                "discovered source line range is invalid; "
                f"line_count={len(lines)}"
            )
        observed_content = "\n".join(lines[line_start - 1 : line_end])
        if len(observed_content) > MAX_DISCOVERY_OBSERVATION_CHARS:
            raise ResearchSourceDiscoveryInputError(
                "discovered source line range exceeds the observation limit; "
                "request a smaller range"
            )
    else:
        observed_content = content[:MAX_DISCOVERY_OBSERVATION_CHARS]
    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    citation_ref = "public-research-source-ref:" + stable_hash(
        {
            "provider": provider,
            "source_identity": source_identity,
            "revision": revision,
            "path": path,
            "content_sha256": content_sha256,
        }
    )
    observation = {
        "ok": True,
        "provider": provider,
        "source_handle": source_handle,
        "source_kind": source_kind,
        "title": title,
        "url": url,
        "publication_date": publication_date,
        "citation": citation,
        "revision": revision,
        "path": path,
        "content": observed_content,
        "content_sha256": content_sha256,
        "content_line_count": len(lines),
        "content_truncated": (
            (
                range_requested
                and (line_start != 1 or line_end != len(lines))
            )
            or (
                not range_requested
                and len(content) > len(observed_content)
            )
        ),
        "citation_ref": citation_ref,
        "proof_evidence_status": RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE,
        "boundary": (
            "This is an exact bounded observation from a model-selected public source. "
            "It is literature/code evidence, not independent review, execution evidence, "
            "or mathematical proof."
        ),
    }
    if range_requested:
        observation.update(
            {
                "line_start": line_start,
                "line_end": line_end,
                "content_range_sha256": hashlib.sha256(
                    observed_content.encode("utf-8")
                ).hexdigest(),
            }
        )
    return observation


def _round_robin_rows(
    groups: Sequence[Sequence[dict[str, Any]]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    while len(rows) < limit and any(index < len(group) for group in groups):
        for group in groups:
            if index < len(group):
                rows.append(dict(group[index]))
                if len(rows) >= limit:
                    break
        index += 1
    return rows


def _first_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        for item in value:
            text = str(item or "").strip()
            if text:
                return text
    return ""


def _arxiv_atom_rows(raw: bytes) -> list[dict[str, Any]]:
    upper = raw[:4_096].upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ResearchSourceDiscoveryError(
            "arXiv Atom response contains a prohibited XML declaration"
        )
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ResearchSourceDiscoveryError(
            "arXiv returned invalid Atom XML"
        ) from exc

    atom = "{" + ARXIV_ATOM_NAMESPACE + "}"
    rows: list[dict[str, Any]] = []
    observed_ids: set[str] = set()
    for entry in root.findall(atom + "entry"):
        entry_url = str(entry.findtext(atom + "id", default="") or "").strip()
        path = urllib.parse.urlparse(entry_url).path
        arxiv_id = path.split("/abs/", 1)[-1] if "/abs/" in path else ""
        if not ARXIV_IDENTIFIER_PATTERN.fullmatch(arxiv_id):
            continue
        normalized_id = arxiv_id.lower()
        if normalized_id in observed_ids:
            continue
        published = str(
            entry.findtext(atom + "published", default="") or ""
        )[:10]
        updated = str(entry.findtext(atom + "updated", default="") or "")[:10]
        try:
            date.fromisoformat(published)
            date.fromisoformat(updated)
        except ValueError:
            continue
        title = " ".join(
            str(entry.findtext(atom + "title", default="") or "").split()
        )
        summary = " ".join(
            str(entry.findtext(atom + "summary", default="") or "").split()
        )
        authors = [
            " ".join(str(author.findtext(atom + "name", default="") or "").split())
            for author in entry.findall(atom + "author")
        ]
        authors = [author for author in authors if author]
        if not title or not authors:
            continue
        observed_ids.add(normalized_id)
        rows.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "summary": summary,
                "published": published,
                "updated": updated,
            }
        )
    return rows


def _arxiv_citation(item: Mapping[str, Any]) -> str:
    authors = item.get("authors", [])
    author_text = ", ".join(
        str(author) for author in authors if str(author).strip()
    ) if isinstance(authors, list) else ""
    return ". ".join(
        part
        for part in (
            author_text,
            str(item.get("title", "") or ""),
            str(item.get("published", "") or "")[:4],
            "arXiv:" + str(item.get("arxiv_id", "") or ""),
        )
        if part
    )


def _crossref_publication_date(item: Mapping[str, Any]) -> str:
    for key in (
        "published-print",
        "published-online",
        "published",
        "issued",
    ):
        value = item.get(key, {})
        parts_rows = value.get("date-parts", []) if isinstance(value, Mapping) else []
        if not parts_rows or not isinstance(parts_rows[0], list):
            continue
        parts = [int(part) for part in parts_rows[0][:3] if isinstance(part, int)]
        if not parts:
            continue
        year = parts[0]
        month = parts[1] if len(parts) > 1 else 1
        day = parts[2] if len(parts) > 2 else 1
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            continue
    return ""


def _crossref_authors(item: Mapping[str, Any]) -> list[str]:
    rows = item.get("author", [])
    authors: list[str] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        name = " ".join(
            part
            for part in (
                str(row.get("given", "") or "").strip(),
                str(row.get("family", "") or "").strip(),
            )
            if part
        )
        if name:
            authors.append(name)
    return authors


def _crossref_citation(item: Mapping[str, Any]) -> str:
    title = _first_text(item.get("title"))
    authors = _crossref_authors(item)
    publication_date = _crossref_publication_date(item)
    venue = _first_text(item.get("container-title"))
    doi = str(item.get("DOI", "") or "").strip()
    return ". ".join(
        part
        for part in (
            ", ".join(authors),
            title,
            venue,
            publication_date[:4],
            f"doi:{doi}" if doi else "",
        )
        if part
    )


def _crossref_markdown(item: Mapping[str, Any], *, fallback_doi: str) -> str:
    title = _first_text(item.get("title")) or fallback_doi
    doi = str(item.get("DOI", "") or fallback_doi).strip()
    authors = _crossref_authors(item)
    venue = _first_text(item.get("container-title"))
    publication_date = _crossref_publication_date(item)
    abstract = _clean_markup(str(item.get("abstract", "") or ""))
    links = []
    for row in item.get("link", []) if isinstance(item.get("link"), list) else []:
        if isinstance(row, Mapping) and str(row.get("URL", "") or "").strip():
            links.append(str(row["URL"]).strip())
    lines = [
        f"# {title}",
        "",
        f"- DOI: {doi}",
        f"- URL: {str(item.get('URL', '') or f'https://doi.org/{doi}')}",
        f"- Authors: {', '.join(authors)}",
        f"- Venue: {venue}",
        f"- Publication date: {publication_date}",
    ]
    if links:
        lines.append("- Deposited resource links: " + ", ".join(links[:10]))
    lines.extend(["", "## Deposited abstract", "", abstract or "Not supplied by Crossref."])
    return "\n".join(lines).strip() + "\n"


def _clean_markup(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", html.unescape(no_tags)).strip()


def _normalized_repository_path(value: str) -> str:
    normalized = str(value or "").strip().replace("\\", "/")
    if not normalized:
        return ""
    parts = normalized.split("/")
    if normalized.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise ResearchSourceDiscoveryInputError(
            "repository path must be a relative normalized path"
        )
    if len(normalized) > 1_000:
        raise ResearchSourceDiscoveryInputError("repository path is too long")
    return normalized


def _acquired_repository_content(
    snapshot: ResearchSourceSnapshot, path: str,
) -> tuple[str | list[dict[str, str]], bool]:
    for document in snapshot.documents:
        if document.relative_path != path:
            continue
        if document.content_mode != "text" or document.file_mode == "120000":
            raise ResearchSourceDiscoveryInputError("selected repository file is not a regular UTF-8 text file")
        try:
            raw = snapshot.document_path(document.document_id).read_bytes()
        except (OSError, ValueError) as exc:
            raise ResearchSourceDiscoveryError(f"acquired repository is unavailable: {exc}") from exc
        if hashlib.sha256(raw).hexdigest() != document.sha256:
            raise ResearchSourceDiscoveryError("acquired repository is unavailable: source file bytes changed")
        return raw.decode("utf-8"), False
    directory = PurePosixPath(path)
    children: dict[str, str] = {}
    for document in snapshot.documents:
        relative = PurePosixPath(document.relative_path)
        if not relative.is_relative_to(directory):
            continue
        parts = relative.relative_to(directory).parts
        children[str(directory / parts[0])] = "dir" if len(parts) > 1 else "file"
    if not children:
        raise ResearchSourceDiscoveryInputError("selected repository path does not exist")
    return [{"path": name, "type": kind} for name, kind in sorted(children.items())], True


def _github_directory_markdown(
    repository: str,
    revision: str,
    directory: str,
    listing: Sequence[Any],
    *,
    description: str = "",
) -> str:
    rows = []
    for item in listing:
        if not isinstance(item, Mapping):
            continue
        path = str(item.get("path", item.get("name", "")) or "").strip()
        kind = str(item.get("type", "") or "").strip()
        if path:
            rows.append(f"- {kind or 'entry'}: `{path}`")
    metadata = [f"- Pinned commit: `{revision}`"]
    if directory:
        metadata.append(f"- Directory: `{directory}`")
    elif description:
        metadata.append(f"- Description: {description}")
    heading = repository + (f": {directory}" if directory else "")
    section = "Entries" if directory else "Root entries"
    empty = "directory" if directory else "root"
    return "\n".join([
        f"# {heading}", "", *metadata, "", f"## {section}", "",
        *(rows or [f"- No {empty} entries returned."]),
    ]).strip() + "\n"
