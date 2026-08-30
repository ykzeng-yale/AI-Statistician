from __future__ import annotations

import base64
import hashlib
import html
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Mapping, Protocol, Sequence

from .fingerprint import stable_hash


RESEARCH_SOURCE_DISCOVERY_SEARCH_TOOL = "discover_research_sources"
RESEARCH_SOURCE_DISCOVERY_READ_TOOL = "read_discovered_research_source"
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


class ResearchSourceDiscoveryError(RuntimeError):
    """A provider/network failure that the research model must not repair."""


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
        self._results: dict[str, dict[str, Any]] = {}
        self._allowed_github_revisions: dict[str, set[str]] = {}
        self._arxiv_html_cache: dict[str, str] = {}

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
            "strict_historical_benchmark_authority": False,
            "secret_values_model_visible": False,
            "proof_evidence_status": (
                RESEARCH_SOURCE_DISCOVERY_NOT_PROOF_EVIDENCE
            ),
            "boundary": (
                "Live public API observations can ground literature and repository "
                "scouting. Exact-version arXiv HTML is preprint text, not publication "
                "authority. These observations are not a frozen benchmark corpus, "
                "independent review, replication evidence, or mathematical proof."
            ),
        }

    def new_session(self) -> PublicResearchSourceDiscovery:
        """Return the same provider policy with isolated model-visible handles."""

        return PublicResearchSourceDiscovery(
            config=self.config,
            github_token=self._github_token,
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
        for row in rows:
            self._results[str(row["source_handle"])] = dict(row)
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
        row = self._results.get(normalized_handle)
        if row is None:
            raise ResearchSourceDiscoveryInputError(
                "discovered source handle is unknown in this model session; search first"
            )
        if row["source_kind"] == "paper":
            if str(path or "").strip() or str(revision or "").strip():
                raise ResearchSourceDiscoveryInputError(
                    "paper discovery reads do not accept path or revision"
                )
            return self._read_crossref(
                row,
                line_start=line_start,
                line_end=line_end,
            )
        if row["source_kind"] == "preprint":
            if str(path or "").strip() or str(revision or "").strip():
                raise ResearchSourceDiscoveryInputError(
                    "preprint discovery reads do not accept path or revision"
                )
            return self._read_arxiv(
                row,
                line_start=line_start,
                line_end=line_end,
            )
        return self._read_github(
            row,
            path=str(path or "").strip(),
            revision=str(revision or "").strip(),
            line_start=line_start,
            line_end=line_end,
        )

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

    def _read_crossref(
        self,
        row: Mapping[str, Any],
        *,
        line_start: int,
        line_end: int,
    ) -> dict[str, Any]:
        doi = str(row["doi"])
        payload = self._json_fetcher(
            "https://api.crossref.org/works/"
            + urllib.parse.quote(doi, safe=""),
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
        content = _crossref_markdown(item, fallback_doi=doi)
        return _source_read_observation(
            provider=self.provider_name,
            source_handle=str(row["source_handle"]),
            source_kind="paper",
            source_identity=str(row["source_identity"]),
            title=_first_text(item.get("title")) or str(row["title"]),
            url=str(item.get("URL", "") or row["url"]),
            publication_date=publication_date,
            citation=_crossref_citation(item) or str(row["citation"]),
            revision="crossref-record:" + stable_hash(item)[:24],
            path="metadata.md",
            content=content,
            line_start=line_start,
            line_end=line_end,
        )

    def _read_arxiv(
        self,
        row: Mapping[str, Any],
        *,
        line_start: int,
        line_end: int,
    ) -> dict[str, Any]:
        arxiv_id = str(row["arxiv_id"])
        url = "https://arxiv.org/html/" + urllib.parse.quote(
            arxiv_id,
            safe="/.",
        )
        content = self._arxiv_html_cache.get(arxiv_id)
        if content is None:
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
                raise ResearchSourceDiscoveryError(
                    "arXiv HTML is not UTF-8 text"
                ) from exc
            if not re.search(r"<html(?:\s|>)", content, flags=re.IGNORECASE):
                raise ResearchSourceDiscoveryError(
                    "arXiv returned a non-HTML paper representation"
                )
            self._arxiv_html_cache[arxiv_id] = content
        return _source_read_observation(
            provider=self.provider_name,
            source_handle=str(row["source_handle"]),
            source_kind="preprint",
            source_identity=str(row["source_identity"]),
            title=str(row["title"]),
            url=url,
            publication_date=str(row["publication_date"]),
            citation=str(row["citation"]),
            revision=arxiv_id,
            path="paper.html",
            content=content,
            line_start=line_start,
            line_end=line_end,
        )

    def _read_github(
        self,
        row: Mapping[str, Any],
        *,
        path: str,
        revision: str,
        line_start: int,
        line_end: int,
    ) -> dict[str, Any]:
        repository = str(row["repository"])
        normalized_path = _normalized_repository_path(path)
        allowed_revisions = self._allowed_github_revisions.setdefault(
            str(row["source_handle"]), set()
        )
        if revision:
            if revision not in allowed_revisions:
                raise ResearchSourceDiscoveryInputError(
                    "GitHub revision was not resolved for this source in the current session"
                )
            resolved_revision = revision
        else:
            resolved_revision = self._github_revision_at_horizon(repository)
            allowed_revisions.add(resolved_revision)

        quoted_repo = "/".join(
            urllib.parse.quote(part, safe="") for part in repository.split("/")
        )
        if normalized_path:
            quoted_path = urllib.parse.quote(normalized_path, safe="/")
            payload = self._json_fetcher(
                f"https://api.github.com/repos/{quoted_repo}/contents/{quoted_path}?"
                + urllib.parse.urlencode({"ref": resolved_revision}),
                self._github_headers(),
                self.config.timeout_seconds,
            )
            if not isinstance(payload, Mapping) or payload.get("encoding") != "base64":
                raise ResearchSourceDiscoveryInputError(
                    "selected repository file has no inline base64 content"
                )
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
            listing = self._json_fetcher(
                f"https://api.github.com/repos/{quoted_repo}/contents?"
                + urllib.parse.urlencode({"ref": resolved_revision}),
                self._github_headers(),
                self.config.timeout_seconds,
            )
            content = _github_root_markdown(
                repository,
                resolved_revision,
                listing if isinstance(listing, list) else [],
                description=str(row.get("summary", "") or ""),
            )
            pinned_url = f"https://github.com/{repository}/tree/{resolved_revision}"
        return _source_read_observation(
            provider=self.provider_name,
            source_handle=str(row["source_handle"]),
            source_kind="repository",
            source_identity=str(row["source_identity"]),
            title=str(row["title"]),
            url=pinned_url,
            publication_date=str(row.get("publication_date", "") or ""),
            citation=f"{row['citation']} at commit {resolved_revision}",
            revision=resolved_revision,
            path=normalized_path or ".",
            content=content,
            line_start=line_start,
            line_end=line_end,
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

    def _crossref_headers(self) -> dict[str, str]:
        contact = (
            f"; mailto:{self.config.contact_email}"
            if self.config.contact_email
            else ""
        )
        return {
            "User-Agent": (
                "AI-Statistician/0.1 "
                "(https://github.com/ykzeng-yale/AI-Statistician"
                + contact
                + ")"
            ),
        }

    def _github_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "ykzeng-yale-AI-Statistician",
        }
        if self._github_token:
            headers["Authorization"] = "Bearer " + self._github_token
        return headers

    def _arxiv_headers(self) -> dict[str, str]:
        contact = (
            f"; mailto:{self.config.contact_email}"
            if self.config.contact_email
            else ""
        )
        return {
            "User-Agent": (
                "AI-Statistician/0.1 "
                "(https://github.com/ykzeng-yale/AI-Statistician"
                + contact
                + ")"
            )
        }


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
            "repository path must be a relative normalized file path"
        )
    if len(normalized) > 1_000:
        raise ResearchSourceDiscoveryInputError("repository path is too long")
    return normalized


def _github_root_markdown(
    repository: str,
    revision: str,
    listing: Sequence[Any],
    *,
    description: str,
) -> str:
    rows = []
    for item in listing:
        if not isinstance(item, Mapping):
            continue
        path = str(item.get("path", item.get("name", "")) or "").strip()
        kind = str(item.get("type", "") or "").strip()
        if path:
            rows.append(f"- {kind or 'entry'}: `{path}`")
    return "\n".join(
        [
            f"# {repository}",
            "",
            f"- Pinned commit: `{revision}`",
            f"- Description: {description}",
            "",
            "## Root entries",
            "",
            *(rows or ["- No root entries returned."]),
        ]
    ).strip() + "\n"
