from __future__ import annotations

import hashlib
import urllib.parse

import pytest

from ai_statistician.research_source_discovery import (
    MAX_DISCOVERY_OBSERVATION_CHARS,
    PublicResearchSourceDiscovery,
    PublicResearchSourceDiscoveryConfig,
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


@pytest.mark.parametrize("source_horizon", ["", "2025/01/01", "not-a-date"])
def test_public_discovery_requires_explicit_iso_source_horizon(
    source_horizon: str,
) -> None:
    with pytest.raises(ValueError, match="ISO date"):
        PublicResearchSourceDiscoveryConfig(source_horizon=source_horizon)
