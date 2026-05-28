# EmpericalProcessLEAN Source Pool

This folder vendors the `StatInference/` tree from
`ykzeng-yale/EmpericalProcessLEAN` main.

Snapshot:

- Repository: `https://github.com/ykzeng-yale/EmpericalProcessLEAN`
- Commit: `a8b1fcae3a040c2531281e467f75b6808f71848d`
- Vendored scope: `StatInference/`, `StatInference.lean`, `lakefile.lean`,
  and `lean-toolchain`

Purpose:

- Feed the AI Statistician formal-source index with the current shared
  statistics/probability foundations from EmpericalProcessLEAN.
- Reuse existing VdVW empirical-process primitives, Durrett probability
  modules, Vaart asymptotic-statistics wrappers, probability-measure
  foundations, matching/WDSM bridges, and optimization interfaces before
  inventing new local definitions.

This is a read-only source pool for retrieval and proof-bank expansion. The
active AI Statistician runtime remains the top-level `ai_statistician/` package.
