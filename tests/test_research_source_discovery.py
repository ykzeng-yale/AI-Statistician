from __future__ import annotations

import hashlib
import json
import sqlite3
import urllib.parse

import pytest

from ai_statistician.research_source_discovery import (
    MAX_DISCOVERY_OBSERVATION_CHARS,
    PublicResearchSourceDiscovery,
    PublicResearchSourceDiscoveryConfig,
    RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
    RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL,
    ResearchSourceDiscoveryError,
    ResearchSourceDiscoveryInputError,
    execute_research_source_discovery_client_tool,
    research_source_discovery_client_tools,
)


def test_acquired_repository_is_exact_durable_and_readable_without_network(discovered_repository, monkeypatch):
    fixture = discovered_repository
    discovery, handle, revision = (fixture[key] for key in ("discovery", "handle", "revision"))
    with pytest.raises(ResearchSourceDiscoveryInputError, match="discovered repository"):
        discovery.acquire_repository(handle, revision=revision)
    discovery.search("fixture", source_kind="repository")
    with pytest.raises(ResearchSourceDiscoveryInputError, match="resolved revision"):
        discovery.acquire_repository(handle, revision=revision)
    discovery.read(handle)
    with pytest.raises(ResearchSourceDiscoveryInputError, match="resolved revision"):
        discovery.acquire_repository(handle, revision="a" * 40)

    observation, ref, error = execute_research_source_discovery_client_tool(
        discovery, tool_name=RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL,
        tool_input={"source_handle": handle, "revision": revision},
    )
    assert not error and ref["snapshot"]["document_count"] == len(fixture["files"])
    assert ref["snapshot"]["repository_identity"]["git_commit"] == revision
    assert "content" not in ref and "manifest_path" not in ref["snapshot"]
    assert "NOT_PROOF_EVIDENCE" in ref["proof_evidence_status"]
    assert fixture["acquisitions"][0]["source_horizon"] == "2025-12-31"
    assert fixture["acquisitions"][0]["repository_url"] == "https://github.com/fixture/project"
    resumed = discovery.new_session()
    monkeypatch.setattr(resumed, "_json_fetcher", lambda *_: pytest.fail("acquired project must read offline"))
    assert resumed.acquire_repository(handle, revision=revision) == observation
    assert len(fixture["acquisitions"]) == 1
    assert "pkg/method.py" in resumed.read(handle, revision=revision, path="pkg")["content"]
    assert resumed.read(handle, revision=revision, path="pkg/method.py")["content"] == fixture["files"]["pkg/method.py"]
    assert resumed.read(handle, revision=revision, path="pkg/__init__.py")["content"] == ""
    with pytest.raises(ResearchSourceDiscoveryInputError, match="UTF-8"):
        resumed.read(handle, revision=revision, path="assets/raw.bin")
    with pytest.raises(ResearchSourceDiscoveryInputError, match="does not exist"):
        resumed.read(handle, revision=revision, path="missing.py")

    snapshot_dir = fixture["acquisitions"][0]["output_dir"]
    (snapshot_dir / "repository/pkg/method.py").write_text("changed bytes\n")
    for action in (
        lambda: resumed.read(handle, revision=revision, path="pkg/method.py"),
        lambda: resumed.acquire_repository(handle, revision=revision),
    ):
        with pytest.raises(ResearchSourceDiscoveryError, match="unavailable"):
            action()
    assert len(fixture["acquisitions"]) == 1


def test_acquisition_tool_reports_failure_without_repair_or_authority(discovered_repository, monkeypatch):
    from ai_statistician import research_source_discovery as module

    discovery = discovered_repository["discovery"]
    handle, revision = discovered_repository["handle"], discovered_repository["revision"]
    discovery.search("fixture", source_kind="repository")
    discovery.read(handle)
    diagnostic = "unfamiliar acquisition diagnostic: " + "q" * 1500

    def fail(**_kwargs):
        raise ValueError(diagnostic)

    monkeypatch.setattr(module, "acquire_public_github_repository_snapshot", fail)
    observation, ref, error = execute_research_source_discovery_client_tool(
        discovery, tool_name=RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL,
        tool_input={"source_handle": handle, "revision": revision},
    )
    assert error and not ref and observation["detail"] == diagnostic
    assert not discovery._observations.snapshot(handle, revision)
    for extra in ({"output_dir": "/tmp/other"}, {"source_horizon": "2099-01-01"}):
        with pytest.raises(ResearchSourceDiscoveryInputError, match="accepts only"):
            execute_research_source_discovery_client_tool(
                discovery, tool_name=RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL,
                tool_input={"source_handle": handle, "revision": revision, **extra},
            )
    assert RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL not in {
        tool.name for tool in research_source_discovery_client_tools()
    }
    assert RESEARCH_SOURCE_DISCOVERY_ACQUIRE_TOOL in {
        tool.name for tool in research_source_discovery_client_tools(repository_acquisition=True)
    }


def test_acquired_manifest_cannot_change_its_pinned_descriptor(discovered_repository, monkeypatch):
    from ai_statistician import research_source_discovery as module

    fixture = discovered_repository
    discovery, handle, revision = (fixture[key] for key in ("discovery", "handle", "revision"))
    discovery.search("fixture", source_kind="repository")
    discovery.read(handle)
    discovery.acquire_repository(handle, revision=revision)
    manifest = fixture["acquisitions"][0]["output_dir"] / "sources.json"
    payload = json.loads(manifest.read_text())
    payload["snapshot_id"] = "different-source-identity"
    manifest.write_text(json.dumps(payload))
    monkeypatch.setattr(module, "load_research_source_snapshot", lambda *_: pytest.fail("reject changed manifest before opening its files"))
    with pytest.raises(ResearchSourceDiscoveryError, match="snapshot identity changed"):
        discovery.new_session().read(handle, revision=revision, path="pkg/method.py")


def test_public_paper_discovery_is_horizon_bound_and_handle_scoped() -> None:
    requests: list[tuple[str, dict[str, str]]] = []

    def fetch_json(url, headers, timeout):
        del timeout
        requests.append((url, dict(headers)))
        if "/works?" in url:
            return {
                "message": {
                    "items": [
                        {
                            "DOI": "10.1000/robust",
                            "title": ["A robust estimator"],
                            "author": [{"given": "Ada", "family": "Stone"}],
                            "published": {"date-parts": [[2024, 5, 2]]},
                            "container-title": ["Journal of Examples"],
                            "URL": "https://doi.org/10.1000/robust",
                            "abstract": "<jats:p>Finite variance result.</jats:p>",
                        },
                        {
                            "DOI": "10.1000/future",
                            "title": ["A future answer"],
                            "published": {"date-parts": [[2026, 1, 1]]},
                        },
                    ]
                }
            }
        assert url.endswith("/works/10.1000%2Frobust")
        return {
            "message": {
                "DOI": "10.1000/robust",
                "title": ["A robust estimator"],
                "author": [{"given": "Ada", "family": "Stone"}],
                "published": {"date-parts": [[2024, 5, 2]]},
                "container-title": ["Journal of Examples"],
                "URL": "https://doi.org/10.1000/robust",
                "abstract": "<jats:p>Finite variance result.</jats:p>",
            }
        }

    provider = PublicResearchSourceDiscovery(
        config=PublicResearchSourceDiscoveryConfig(
            source_horizon="2025-12-31",
            contact_email="research@example.org",
        ),
        github_token="secret-token",
        json_fetcher=fetch_json,
    )

    search = provider.search("robust finite variance", source_kind="paper", top_k=3)

    assert len(search["results"]) == 1
    result = search["results"][0]
    assert result["title"] == "A robust estimator"
    assert "10.1000" not in result["source_handle"]
    assert search["source_horizon"] == "2025-12-31"
    query = urllib.parse.parse_qs(urllib.parse.urlparse(requests[0][0]).query)
    assert query["filter"] == ["until-pub-date:2025-12-31"]
    assert query["mailto"] == ["research@example.org"]
    assert "secret-token" not in str(provider.descriptor())

    referee_session = provider.new_session()
    assert referee_session is not provider
    assert referee_session.descriptor() == provider.descriptor()
    with pytest.raises(ResearchSourceDiscoveryInputError, match="search first"):
        referee_session.read(result["source_handle"])

    read = provider.read(result["source_handle"])

    assert "Finite variance result." in read["content"]
    assert "<jats:p>" not in read["content"]
    assert read["content_sha256"] == hashlib.sha256(
        read["content"].encode("utf-8")
    ).hexdigest()
    assert read["citation_ref"].startswith("public-research-source-ref:")
    with pytest.raises(ResearchSourceDiscoveryInputError, match="search first"):
        provider.read("public-source:unknown")


def test_public_repository_discovery_pins_horizon_commit_before_file_reads(
    tmp_path,
) -> None:
    revision = "a" * 40
    source_body = (
        b"def estimate(data):\n    return sum(data) / len(data)\n"
        + b"# supporting source context\n" * 2_500
    )
    json_requests: list[tuple[str, dict[str, str]]] = []

    def fetch_json(url, headers, timeout):
        del timeout
        json_requests.append((url, dict(headers)))
        if "/search/repositories?" in url:
            return {
                "items": [
                    {
                        "full_name": "stats/example-method",
                        "default_branch": "main",
                        "html_url": "https://github.com/stats/example-method",
                        "created_at": "2020-04-01T00:00:00Z",
                        "description": "Reference implementation",
                    }
                ]
            }
        if "/commits?" in url:
            return [{"sha": revision}]
        if "/contents/src/estimator.py?" in url:
            import base64

            return {
                "encoding": "base64",
                "content": base64.b64encode(source_body).decode("ascii"),
            }
        if "/contents/src?" in url:
            return [
                {"type": "file", "path": "src/estimator.py"},
                {"type": "dir", "path": "src/helpers"},
            ]
        assert "/contents?" in url
        return [
            {"type": "file", "path": "README.md"},
            {"type": "dir", "path": "src"},
        ]

    provider = PublicResearchSourceDiscovery(
        config=PublicResearchSourceDiscoveryConfig(source_horizon="2025-06-30"),
        github_token="secret-token",
        state_dir=tmp_path / "repository-observations",
        json_fetcher=fetch_json,
    )

    search = provider.search(
        "statistical estimator", source_kind="repository", top_k=2
    )
    handle = search["results"][0]["source_handle"]
    root = provider.read(handle)

    assert root["revision"] == revision
    assert "`src`" in root["content"]
    commit_query = urllib.parse.parse_qs(
        urllib.parse.urlparse(
            next(url for url, _ in json_requests if "/commits?" in url)
        ).query
    )
    assert commit_query["until"] == ["2025-06-30T23:59:59Z"]

    source_directory = provider.read(handle, path="src", revision=revision)

    assert source_directory["revision"] == revision
    assert source_directory["path"] == "src"
    assert "`src/estimator.py`" in source_directory["content"]
    assert "`src/helpers`" in source_directory["content"]
    assert f"/tree/{revision}/src" in source_directory["url"]
    assert source_directory["content_sha256"] == hashlib.sha256(
        source_directory["content"].encode("utf-8")
    ).hexdigest()
    observed_directory, directory_ref, model_error = (
        execute_research_source_discovery_client_tool(
            provider,
            tool_name=RESEARCH_SOURCE_DISCOVERY_READ_TOOL,
            tool_input={
                "source_handle": handle,
                "path": "src",
                "revision": revision,
            },
        )
    )
    assert model_error is False
    assert observed_directory == source_directory
    assert directory_ref["revision"] == revision
    assert directory_ref["path"] == "src"
    assert directory_ref["content_sha256"] == source_directory["content_sha256"]
    assert "content" not in directory_ref

    source = provider.read(handle, path="src/estimator.py", revision=revision)

    assert "def estimate" in source["content"]
    assert len(source["content"]) == MAX_DISCOVERY_OBSERVATION_CHARS
    assert source["content_truncated"] is True
    assert source["content_sha256"] == hashlib.sha256(source_body).hexdigest()
    assert f"/blob/{revision}/src/estimator.py" in source["url"]
    source_headers = next(
        headers
        for url, headers in json_requests
        if "/contents/src/estimator.py?" in url
    )
    assert source_headers["Authorization"] == "Bearer secret-token"
    assert "secret-token" not in str(source)

    request_count = len(json_requests)
    resumed = PublicResearchSourceDiscovery(
        config=PublicResearchSourceDiscoveryConfig(source_horizon="2025-06-30"),
        state_dir=tmp_path / "repository-observations",
        json_fetcher=lambda *_args: pytest.fail(
            "pinned repository observations must reopen without network"
        ),
    )
    assert resumed.read(handle, path="src", revision=revision) == source_directory
    assert resumed.read(
        handle, path="src/estimator.py", revision=revision
    ) == source
    assert len(json_requests) == request_count

    with pytest.raises(ResearchSourceDiscoveryInputError, match="not resolved"):
        provider.read(handle, path="README.md", revision="b" * 40)
    with pytest.raises(ResearchSourceDiscoveryInputError, match="relative normalized"):
        provider.read(handle, path="../secret", revision=revision)


def test_public_preprint_discovery_reads_exact_horizon_bound_arxiv_html() -> None:
    allowed_html = (
        b"<!doctype html>\n<html><body>\n<h1>Exact theorem</h1>\n"
        b"<p>The estimator is asymptotically normal.</p>\n</body></html>"
    )
    atom = b"""<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <entry>
    <id>https://arxiv.org/abs/2401.01234v2</id>
    <title>An exact statistical preprint</title>
    <updated>2025-01-03T12:00:00Z</updated>
    <published>2024-01-02T12:00:00Z</published>
    <summary>A complete derivation and implementation.</summary>
    <author><name>Ada Stone</name></author>
  </entry>
  <entry>
    <id>https://arxiv.org/abs/2402.05678v3</id>
    <title>A post-horizon revision</title>
    <updated>2026-01-03T12:00:00Z</updated>
    <published>2024-02-02T12:00:00Z</published>
    <summary>This latest version is not horizon safe.</summary>
    <author><name>Grace Vale</name></author>
  </entry>
</feed>"""
    requests: list[tuple[str, dict[str, str], int]] = []
    pacing: list[str] = []

    def fetch_bytes(url, headers, timeout, max_bytes):
        del timeout
        requests.append((url, dict(headers), max_bytes))
        return atom if "export.arxiv.org/api/query" in url else allowed_html

    provider = PublicResearchSourceDiscovery(
        config=PublicResearchSourceDiscoveryConfig(
            source_horizon="2025-12-31",
            contact_email="research@example.org",
        ),
        json_fetcher=lambda *_args: pytest.fail("JSON provider was not requested"),
        bytes_fetcher=fetch_bytes,
        arxiv_request_pacer=lambda: pacing.append("paced"),
    )

    search = provider.search(
        "asymptotic normal estimator",
        source_kind="preprint",
        top_k=3,
    )

    assert len(search["results"]) == 1
    result = search["results"][0]
    assert result["source_kind"] == "preprint"
    assert result["url"].endswith("/html/2401.01234v2")
    assert "2401.01234" not in result["source_handle"]
    search_query = urllib.parse.parse_qs(
        urllib.parse.urlparse(requests[0][0]).query
    )["search_query"][0]
    assert "submittedDate:[199101010000 TO 202512312359]" in search_query

    read = provider.read(result["source_handle"])

    assert read["revision"] == "2401.01234v2"
    assert read["path"] == "paper.html"
    assert read["content"] == allowed_html.decode("utf-8")
    assert read["content_sha256"] == hashlib.sha256(allowed_html).hexdigest()
    assert read["content_line_count"] == 5
    assert read["content_truncated"] is False
    assert requests[1][0] == "https://arxiv.org/html/2401.01234v2"
    assert requests[1][1]["User-Agent"].endswith(
        "; mailto:research@example.org)"
    )
    assert pacing == ["paced", "paced"]

    exact_range = provider.read(
        result["source_handle"],
        line_start=2,
        line_end=4,
    )

    expected_range = "\n".join(allowed_html.decode("utf-8").splitlines()[1:4])
    assert exact_range["content"] == expected_range
    assert exact_range["line_start"] == 2
    assert exact_range["line_end"] == 4
    assert exact_range["content_range_sha256"] == hashlib.sha256(
        expected_range.encode("utf-8")
    ).hexdigest()
    assert exact_range["content_truncated"] is True
    assert len(requests) == 2
    assert pacing == ["paced", "paced"]
    assert provider.descriptor()["source_kinds"] == [
        "paper",
        "preprint",
        "repository",
    ]
    with pytest.raises(ResearchSourceDiscoveryInputError, match="do not accept path"):
        provider.read(result["source_handle"], path="paper.tex")


def test_durable_public_source_observation_reopens_without_network(tmp_path) -> None:
    work = {
        "DOI": "10.1000/durable",
        "title": ["A durable exact source"],
        "author": [{"given": "Ada", "family": "Stone"}],
        "published": {"date-parts": [[2024, 5, 2]]},
        "container-title": ["Journal of Examples"],
        "URL": "https://doi.org/10.1000/durable",
        "abstract": "<jats:p>Line one.\nLine two.\nLine three.</jats:p>",
    }
    requests: list[str] = []

    def fetch_json(url, headers, timeout):
        del headers, timeout
        requests.append(url)
        return {"message": {"items": [work]}} if "/works?" in url else {
            "message": work
        }

    state_dir = tmp_path / "public-source-state"
    provider = PublicResearchSourceDiscovery(
        config=PublicResearchSourceDiscoveryConfig(source_horizon="2025-12-31"),
        state_dir=state_dir,
        json_fetcher=fetch_json,
    )
    search = provider.search("durable exact source", source_kind="paper")
    handle = search["results"][0]["source_handle"]
    first = provider.read(handle)
    request_count = len(requests)

    resumed = PublicResearchSourceDiscovery(
        config=PublicResearchSourceDiscoveryConfig(source_horizon="2025-12-31"),
        state_dir=state_dir,
        json_fetcher=lambda *_args: pytest.fail(
            "a durable exact observation must not refetch the network"
        ),
    )
    reopened = resumed.read(handle, line_start=1, line_end=3)

    assert len(requests) == request_count
    assert reopened["content"] == "\n".join(first["content"].splitlines()[:3])
    assert reopened["content_sha256"] == first["content_sha256"]
    assert reopened["citation_ref"] == first["citation_ref"]
    assert reopened["content_range_sha256"] == hashlib.sha256(
        reopened["content"].encode("utf-8")
    ).hexdigest()
    assert resumed.descriptor()["durable_exact_observation_store"] is True
    database_path = state_dir / "observations.sqlite3"
    with sqlite3.connect(database_path) as database:
        assert database.execute("SELECT count(*) FROM source_results").fetchone() == (
            1,
        )
        assert database.execute("SELECT count(*) FROM source_reads").fetchone() == (
            1,
        )
        database.execute("UPDATE source_reads SET content = ?", (b"tampered",))

    with pytest.raises(ValueError, match="read identity mismatch"):
        PublicResearchSourceDiscovery(
            config=PublicResearchSourceDiscoveryConfig(
                source_horizon="2025-12-31"
            ),
            state_dir=state_dir,
            json_fetcher=lambda *_args: pytest.fail("network not expected"),
        )


def test_public_preprint_discovery_rejects_unsafe_atom_xml() -> None:
    provider = PublicResearchSourceDiscovery(
        config=PublicResearchSourceDiscoveryConfig(source_horizon="2025-12-31"),
        json_fetcher=lambda *_args: pytest.fail("JSON provider was not requested"),
        bytes_fetcher=lambda *_args: b"<!DOCTYPE feed><feed />",
        arxiv_request_pacer=lambda: None,
    )

    with pytest.raises(ResearchSourceDiscoveryError, match="prohibited XML"):
        provider.search("robust statistics", source_kind="preprint")


@pytest.mark.parametrize("source_horizon", ["", "2025/01/01", "not-a-date"])
def test_public_discovery_requires_explicit_iso_source_horizon(
    source_horizon: str,
) -> None:
    with pytest.raises(ValueError, match="ISO date"):
        PublicResearchSourceDiscoveryConfig(source_horizon=source_horizon)
