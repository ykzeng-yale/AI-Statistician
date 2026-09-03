# Research Source Snapshots

TheoryDeveloper can inspect exact prior papers, code, and documentation without a
separate retrieval agent. Pass a manifest to either canonical entry point:

```bash
ai-statistician research-agent-runtime \
  --research-source-manifest /path/to/sources.json \
  ...
```

For a published repository already acquired locally, freeze the exact tracked tree
from a commit before any model or evaluator run:

```bash
ai-statistician freeze-research-source-project \
  --repository /path/to/local/checkout \
  --revision FULL_COMMIT \
  --snapshot-id published-project-v1 \
  --source-horizon 2026-08-31 \
  --repository-url https://github.com/owner/project \
  --license MIT \
  --out /path/to/frozen-project
```

The freezer reads Git blobs directly from the commit, not mutable worktree files or
`git archive` export rules. It binds every path, Git object ID, executable mode,
byte size, SHA-256, author/committer dates, and aggregate tree identity; a commit
after the declared source horizon is rejected. Nested modules, empty tracked files,
UTF-8 data, and binary execution assets are retained. Symlinks, submodules, oversized
files, path escapes, and output reuse fail before a snapshot is published. Git LFS
pointers remain pointers; required LFS objects must be frozen separately.

```bash
ai-statistician research-architect-theory \
  --research-source-manifest /path/to/sources.json \
  ...
```

The manifest names a directory relative to itself. Hand-authored documents default
to nonempty UTF-8 text and every source is bound to its exact SHA-256. A project
snapshot may additionally declare empty text or a descriptor-only binary execution
asset with exact media, byte, mode, and Git identities. Extract mathematical PDF
content to Markdown for line-addressed reasoning and retain the original PDF identity
in the citation or source log. Pin repository material to a commit.

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
escape, symlink, missing file, hash/blob/mode mismatch, duplicate identity, or absent
`model_visible=true` fails closed. A bounded directory listing exposes direct child
identities, including empty text and binary assets, so a model can navigate an exact
project before searching or reading text. Binary content remains descriptor-only for
the separately pinned source executor. All observations return to the same source owner. Persisted theory evidence stores only the snapshot,
query, document, hash, line-range, and `citation_ref` values; it does not recursively
copy source text. When an authoritative theory document contains a `citation_ref`,
the independent Critic receives that exact hash-verified range transiently for source
comparison. Uncited reads are not copied into Critic context or runtime manifests.

This is a visibility and provenance boundary, not a correctness oracle. The model
must interpret sources, independent review must audit the resulting mathematics,
and Lean kernel evidence remains the only formal proof authority when requested.
Hidden evaluator artifacts and future papers in a historical-rediscovery benchmark
must live outside the snapshot and outside all model-accessible workspaces.

Within a Python/R coding workspace, the same source owner may atomically import
selected observed UTF-8 modules from the frozen snapshot. The import revalidates the
complete snapshot and selected bytes, preserves source and resulting-project hashes,
and changes no project state unless every selected file succeeds. Imported files,
including empty modules, remain unexecuted until the model runs the complete project;
binary and data assets stay in the separately bound replication lane.

A frozen project still does not define an executable environment. Bind it separately
with `--research-source-execution-manifest`: exact interpreter, lock/probe, arguments,
working directory, declared result files, no network, and copy-on-write execution.
Successful execution is source-replication observation only; it is not semantic,
statistical, confirmatory, novelty, or proof authority.
