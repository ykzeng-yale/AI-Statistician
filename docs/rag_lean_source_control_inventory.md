# RAG And Lean Source-Control Inventory

This repository commits source code, reusable Lean source, tests, and small
configuration needed to rebuild RAG and proof artifacts. It does not commit
generated retrieval databases, `runs/` outputs, `.lake` build products,
virtual environments, bytecode caches, or local API/operator notes.

## Tracked RAG And Proof Infrastructure

Core RAG and proof-search implementation is tracked under `ai_statistician/`,
including:

- `formal_source_index.py`, `formal_source_graph.py`, and
  `formal_source_hybrid.py`
- formal-source retrieval benchmarks and ablations
- `retrieval.py`
- `lean_rag_dependency.py`, `lean_rag_dependency_health.py`, and
  `lean_rag_package_audit.py`
- `proof_search.py`, `proof_search_audit.py`,
  `proof_search_retrieval_ablation.py`, `proof_search_kernel_rerun_queue.py`,
  `proof_search_training_export.py`, and `proof_search_value_model.py`
- coverage and reuse diagnostics such as `frontier_coverage_audit.py`,
  `primitive_source_coverage_audit.py`, and `rag_collaboration_export.py`

These are source-control artifacts. Generated indexes and local run evidence
remain rebuildable outputs.

## Tracked Lean Source

Reusable Lean and statistics source is tracked under:

- `Preliminary Attempt/*.lean`
- `legacy_sources/ai_statistician/`
- `legacy_sources/emperical_process_lean/`

As of the July 11, 2026 handoff, the active branch has 836 tracked files
matching:

```bash
git ls-files 'legacy_sources/**/*.lean' \
  'legacy_sources/**/lakefile.lean' \
  'legacy_sources/**/lean-toolchain' \
  'legacy_sources/**/lake-manifest.json' \
  'Preliminary Attempt/*.lean' | wc -l
```

The local source scan excluding `.lake` should not reveal additional untracked
Lean source:

```bash
comm -23 \
  <(find legacy_sources -path '*/.lake' -prune -o \
    \( -name '*.lean' -o -name 'lakefile.lean' -o \
       -name 'lake-manifest.json' -o -name 'lean-toolchain' \) \
    -type f -print | sort) \
  <(git ls-files 'legacy_sources/**' | sort)
```

If this command prints paths, classify them before adding them. Commit genuine
Lean source and Lake configuration; do not commit build products.

## Intentionally Untracked Local Artifacts

The following remain local and ignored:

- `runs/`, including retrieval databases, proof audit outputs, live runtime
  manifests, and benchmark outputs
- `.lake/` build products under any Lean checkout
- `.venv/`, `__pycache__/`, `*.pyc`, and local test caches
- `.tmp_publish/` and other temporary source exports
- `.env`, `.env.local`, API-key inventories, and raw chat-history dumps

These artifacts can be useful evidence for a local investigation, but they are
not portable source-control state. When generated evidence is needed for
coordination, commit a compact manifest, reconstruction command, or source
fixture instead of the raw database or build output.

## Handoff Rule

Before handing work to another Codex task:

1. Run `git status -sb --untracked-files=all`.
2. Run the tracked Lean source check above.
3. Commit and push code, docs, tests, and reusable Lean source to the active
   coordination branch.
4. Report any intentionally excluded generated RAG or Lean artifact paths.

Do not claim RAG or Lean source is missing from GitHub merely because local
generated databases or `.lake` outputs are ignored.
