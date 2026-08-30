from __future__ import annotations

import hashlib
import urllib.parse

import pytest

from ai_statistician.research_source_discovery import (
    MAX_DISCOVERY_OBSERVATION_CHARS,
    PublicResearchSourceDiscovery,
    PublicResearchSourceDiscoveryConfig,
    ResearchSourceDiscoveryError,
    ResearchSourceDiscoveryInputError,
)


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


def test_public_repository_discovery_pins_horizon_commit_before_file_reads() -> None:
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
        assert "/contents?" in url
        return [
            {"type": "file", "path": "README.md"},
            {"type": "file", "path": "src/estimator.py"},
        ]

    provider = PublicResearchSourceDiscovery(
        config=PublicResearchSourceDiscoveryConfig(source_horizon="2025-06-30"),
        github_token="secret-token",
        json_fetcher=fetch_json,
    )

    search = provider.search(
        "statistical estimator", source_kind="repository", top_k=2
    )
    handle = search["results"][0]["source_handle"]
    root = provider.read(handle)

    assert root["revision"] == revision
    assert "`src/estimator.py`" in root["content"]
    commit_query = urllib.parse.parse_qs(
        urllib.parse.urlparse(
            next(url for url, _ in json_requests if "/commits?" in url)
        ).query
    )
    assert commit_query["until"] == ["2025-06-30T23:59:59Z"]

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
