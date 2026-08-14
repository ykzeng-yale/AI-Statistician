# Research Source Snapshots

TheoryDeveloper can inspect exact prior papers, code, and documentation without a
separate retrieval agent. Pass a manifest to either canonical entry point:

```bash
ai-statistician research-agent-runtime \
  --research-source-manifest /path/to/sources.json \
  ...
```

```bash
ai-statistician research-architect-theory \
  --research-source-manifest /path/to/sources.json \
  ...
```

The manifest names a directory relative to itself. Every document is UTF-8 text,
explicitly model-visible, and bound to its exact SHA-256. Extract a PDF to Markdown
or text first and retain the original PDF identity in the citation or source log.
Pin repository material to a commit and record that commit in `git_commit`.

```json
{
  "schema_version": 1,
  "snapshot_id": "published-statistics-through-2025",
  "source_horizon": "2025-12-31",
  "source_root": "public_sources",
  "documents": [
    {
      "document_id": "paper-main-text",
      "title": "Paper title",
      "source_kind": "paper",
      "relative_path": "paper.md",
      "sha256": "64-lowercase-hex-characters",
      "model_visible": true,
      "citation": "Author (2025), Journal",
      "url": "https://example.org/paper",
      "publication_date": "2025-04-01",
      "license": "CC-BY-4.0"
    },
    {
      "document_id": "author-reference-code",
      "title": "Reference implementation",
      "source_kind": "code",
      "relative_path": "code/reference.py",
      "sha256": "64-lowercase-hex-characters",
      "model_visible": true,
      "url": "https://github.com/example/project",
      "git_commit": "full-pinned-commit"
    }
  ]
}
```

The source root and every document path are resolved before the model runs. Path
escape, missing files, hash mismatch, binary/non-UTF-8 content, duplicate identity,
or absent `model_visible=true` fails closed. Search and read observations return to
the same TheoryDeveloper model. Persisted theory evidence stores only the snapshot,
query, document, hash, line-range, and `citation_ref` values; it does not recursively
copy source text. When an authoritative theory document contains a `citation_ref`,
the independent Critic receives that exact hash-verified range transiently for source
comparison. Uncited reads are not copied into Critic context or runtime manifests.

This is a visibility and provenance boundary, not a correctness oracle. The model
must interpret sources, independent review must audit the resulting mathematics,
and Lean kernel evidence remains the only formal proof authority when requested.
Hidden evaluator artifacts and future papers in a historical-rediscovery benchmark
must live outside the snapshot and outside all model-accessible workspaces.
