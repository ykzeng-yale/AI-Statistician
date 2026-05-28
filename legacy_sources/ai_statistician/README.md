# Legacy AI-Statistician Source Pool

This folder vendors the reusable pieces of the old
`ykzeng-yale/AI-Statistician` prototype.

The active runtime is the top-level `ai_statistician/` package. The legacy
source pool is read-only input for retrieval, proof-bank expansion, benchmark
design, and future prover-training data.

Included:

- `StatInference/`: Lean declarations and theorem-shape interfaces for
  asymptotics, estimators, empirical processes, causal inference,
  semiparametric theory, probability measures, and WDSM matching.
- `benchmarks/`: old theorem-hole / benchmark seed files.
- `schemas/`: old JSON schemas for Lean tasks, proof attempts, verification
  reports, and training artifacts.
- `artifacts/training/` and `artifacts/curation/`: old DPO/GRPO/premise and
  theorem-hole curation artifacts.

Excluded:

- Old Python orchestration/runtime code.
- Old worktree and verifier wrappers.
- Old build artifacts, virtual environments, Lake artifacts, PDFs, TeX sources,
  and macOS metadata.

This keeps the new repository self-contained without treating the old system as
the production implementation.
