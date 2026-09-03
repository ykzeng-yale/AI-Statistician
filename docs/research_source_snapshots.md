# Research Source Snapshots

TheoryDeveloper can inspect exact prior papers, code, and documentation without a
separate retrieval agent. Pass a manifest to either canonical entry point:

```bash
ai-statistician research-agent-runtime \
  --research-source-manifest /path/to/sources.json \
  ...
```

For a public GitHub repository, an operator or evaluator can acquire one exact full
commit without ambient credentials and immediately freeze it:

```bash
ai-statistician acquire-public-research-source-project \
  --repository-url https://github.com/owner/project \
  --revision FULL_40_CHARACTER_COMMIT \
  --snapshot-id published-project-v1 \
  --source-horizon 2026-08-31 \
  --license MIT \
  --out /path/to/frozen-project
```

The acquisition uses an empty private Git home, HTTPS only, no credential or prompt
surface, a shallow exact-commit fetch, and a per-blob filter. It verifies the fetched
commit before handing the object database to the local-only freezer. It is an
operator/evaluator command, not model shell authority. For a repository already
acquired locally, freeze the exact tracked tree directly:

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
UTF-8 data, binary execution assets, and relative links to regular files inside the
same exact tree are retained. Absolute, escaping, dangling, directory, chained, or
non-UTF-8 links, submodules, missing or oversized blobs, path escapes, and output
reuse fail before a snapshot is published. Snapshot-time Git reads cannot lazy-fetch
missing objects. Git LFS pointers remain pointers; required LFS objects must be
frozen separately.

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
with `--research-source-execution-manifest`: exact interpreter, lock, arguments,
working directory, declared result files, no network, and copy-on-write execution.
Schema-v3 Python may use the runtime-owned hash-bound version probe so the original
repository need not contain an AI-Statistician helper; other languages require an
explicit snapshot probe document. The manifest records which probe authority ran
and returns its return code, transport errors, exact stream hashes and bounded raw
excerpts to the same Theory source owner even when source execution never starts.
Full probe streams remain in the isolated output files instead of being recursively
copied into model messages or manifests. A hash-checked virtualenv launcher is
resolved for the macOS sandbox without losing its environment identity.
Source stdout and stderr follow the same boundary: the manifest carries exact hashes,
byte counts, truncation status, and bounded excerpts, while the existing result-read
tool can inspect any exact line range from hash-rechecked runtime stream files. This
keeps long published-program logs out of outer tasks and Critic payload copies.
Declared UTF-8 result bodies and previews likewise remain only in their hash-bound
copy-on-write files. Theory scratch code loads selected complete files through the
same verified artifact identity; manifests retain only descriptors and compact CSV
summaries.
Successful execution is source-replication observation only; it is not semantic,
statistical, confirmatory, novelty, or proof authority.
