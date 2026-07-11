# RAG And Lean Source-Control Inventory

This repository should commit source code, reusable Lean source, tests, and
small configuration needed to rebuild RAG/proof artifacts. It should not commit
generated retrieval databases, `runs/` outputs, `.lake` build products,
virtualenvs, bytecode caches, or local API/operator notes.

## Tracked RAG/Proof Infra

The current branch tracks the core RAG and proof-search implementation in
`ai_statistician/`, including:

- `formal_source_index.py`, `formal_source_graph.py`, and
  `formal_source_hybrid.py`
- formal-source retrieval benchmarks and ablations
- `retrieval.py`
- `lean_rag_dependency.py`, `lean_rag_dependency_health.py`, and
  `lean_rag_package_audit.py`
- proof-search modules: `proof_search.py`, `proof_search_audit.py`,
  `proof_search_retrieval_ablation.py`, `proof_search_kernel_rerun_queue.py`,
  `proof_search_training_export.py`, and `proof_search_value_model.py`
- coverage/reuse diagnostics such as `frontier_coverage_audit.py`,
  `primitive_source_coverage_audit.py`, and `rag_collaboration_export.py`

These files are source-control artifacts. They should move through normal
review, tests, and PRs.

## Tracked Lean Source

The repository tracks reusable Lean/statistics source under:

- `Preliminary Attempt/*.lean`
- `legacy_sources/ai_statistician/`
- `legacy_sources/emperical_process_lean/`

As of the July 2026 handoff, the tracked Lean/build-config inventory includes
835 files matching:

```bash
git ls-files 'legacy_sources/**/*.lean' \
  'legacy_sources/**/lakefile.lean' \
  'legacy_sources/**/lean-toolchain' \
  'legacy_sources/**/lake-manifest.json' \
  'Preliminary Attempt/*.lean' | wc -l
```

The local filesystem source scan excluding `.lake` should not reveal additional
untracked Lean source:

```bash
find legacy_sources -path '*/.lake' -prune -o \
  \( -name '*.lean' -o -name 'lakefile.lean' -o \
     -name 'lake-manifest.json' -o -name 'lean-toolchain' \) \
  -type f -print | while read p; do
    git ls-files --error-unmatch "$p" >/dev/null 2>&1 || echo "$p"
  done
```

If this command prints paths, classify them before adding them. Commit genuine
Lean source and Lake config; do not commit build products.

## Intentionally Untracked Local Artifacts

The following are expected to remain local/ignored:

- `runs/`, including `formal_source_index.sqlite`,
  `current_status_lean_rag_dependency_graph/stat_inference.sqlite`, proof audit
  outputs, live runtime manifests, and benchmark outputs
- `.lake/` build products under any Lean checkout
- `.venv/`, `__pycache__/`, `*.pyc`, and local test caches
- `.tmp_publish/` and other temporary source exports
- `.env`, `.env.local`, and API/key inventory notes

These artifacts can be important evidence for a local investigation, but they
are not portable source-control state. If a generated artifact becomes necessary
for coordination, commit a compact manifest, reconstruction command, or source
fixture instead of the raw DB/build output.

## Handoff Rule

Before handing work to another Codex agent:

1. Run `git status -sb --untracked-files=all`.
2. Run the tracked Lean source check above.
3. Push code/docs/tests/Lean source commits to the active PR branch.
4. Report any excluded generated RAG/Lean artifact paths explicitly.

Do not claim RAG or Lean source is missing from GitHub merely because local
generated databases or `.lake` outputs are ignored.
