from __future__ import annotations

import hashlib
import json

import pytest

from ai_statistician.research_source_library import (
    RESEARCH_SOURCE_NOT_PROOF_EVIDENCE,
    load_research_source_snapshot,
)


def _source_snapshot(tmp_path, *, document_overrides=None):
    source_root = tmp_path / "public_sources"
    source_root.mkdir(parents=True)
    source_text = (
        "# A published result\n"
        "\n"
        "Assume independent observations with finite fourth moments.\n"
        "The normalized sample mean converges to a centered Gaussian limit.\n"
        "A plug-in variance estimator is consistent under the same assumptions.\n"
    )
    source_path = source_root / "result.md"
    source_path.write_text(source_text, encoding="utf-8")
    document = {
        "document_id": "published-result",
        "title": "A published result",
        "source_kind": "paper",
        "relative_path": "result.md",
        "sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        "model_visible": True,
        "citation": "Author (2025), Example Journal",
        "url": "https://example.org/result",
        "publication_date": "2025-03-01",
        "license": "CC-BY-4.0",
    }
    document.update(document_overrides or {})
    manifest = {
        "schema_version": 1,
        "snapshot_id": "published-statistics-2025",
        "source_horizon": "2025-12-31",
        "source_root": "public_sources",
        "documents": [document],
    }
    manifest_path = tmp_path / "sources.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path, source_text


def test_hash_bound_source_snapshot_supports_exact_search_and_read(tmp_path) -> None:
    manifest_path, source_text = _source_snapshot(tmp_path)

    snapshot = load_research_source_snapshot(manifest_path)
    search = snapshot.search("finite fourth moments normalized mean", top_k=3)
    read = snapshot.read("published-result", line_start=3, line_end=5)

    assert search["snapshot_hash"] == snapshot.snapshot_hash
    assert search["hits"][0]["document_id"] == "published-result"
    assert "finite fourth moments" in search["hits"][0]["excerpt"]
    assert search["proof_evidence_status"] == RESEARCH_SOURCE_NOT_PROOF_EVIDENCE
    assert read["content"] == "\n".join(source_text.splitlines()[2:5])
    assert read["sha256"] == hashlib.sha256(
        source_text.encode("utf-8")
    ).hexdigest()
    assert read["line_start"] == 3
    assert read["line_end"] == 5
    assert read["citation_ref"].startswith("research-source-ref:")
    assert read["citation_ref"] == snapshot.read(
        "published-result", line_start=3, line_end=5
    )["citation_ref"]
    descriptor = snapshot.descriptor()
    assert descriptor["document_count"] == 1
    assert descriptor["source_horizon"] == "2025-12-31"
    assert descriptor["model_visible"] is True
    assert "relative_path" not in descriptor


def test_source_snapshot_rejects_hash_mismatch(tmp_path) -> None:
    manifest_path, _ = _source_snapshot(
        tmp_path,
        document_overrides={"sha256": "0" * 64},
    )

    with pytest.raises(ValueError, match="sha256 mismatch"):
        load_research_source_snapshot(manifest_path)


def test_source_snapshot_rejects_empty_text(tmp_path) -> None:
    manifest_path, _ = _source_snapshot(tmp_path)
    source_path = tmp_path / "public_sources" / "result.md"
    source_path.write_text("\n", encoding="utf-8")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["documents"][0]["sha256"] = hashlib.sha256(b"\n").hexdigest()
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="must contain nonempty text"):
        load_research_source_snapshot(manifest_path)


def test_source_snapshot_rejects_nonvisible_or_escaping_documents(tmp_path) -> None:
    nonvisible_path, _ = _source_snapshot(
        tmp_path / "nonvisible",
        document_overrides={"model_visible": False},
    )
    with pytest.raises(ValueError, match="model_visible=true"):
        load_research_source_snapshot(nonvisible_path)

    escaping_root = tmp_path / "escaping"
    escaping_root.mkdir()
    hidden_text = "hidden evaluator content\n"
    (escaping_root / "hidden.md").write_text(hidden_text, encoding="utf-8")
    manifest_path, _ = _source_snapshot(
        escaping_root / "snapshot",
        document_overrides={
            "relative_path": "../hidden.md",
            "sha256": hashlib.sha256(hidden_text.encode("utf-8")).hexdigest(),
        },
    )
    with pytest.raises(ValueError, match="stay inside source_root"):
        load_research_source_snapshot(manifest_path)
