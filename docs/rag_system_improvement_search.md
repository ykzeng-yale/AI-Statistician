# RAG System Improvement Search

Date: 2026-06-02.

This note records the next RAG/prover-search improvement direction after the
local source inventory reached Mathlib, StatInference, EmpiricalProcessLEAN,
Atlas, FormalSLT, lean-rademacher, Lean Machine Learning, BrownianMotion,
Kolmogorov extension, SciLean, and the `lean_rag` dependency graph.

## Search Findings

- LeanDojo/ReProver shows that premise selection is a theorem-proving
  bottleneck and that proof-state-aware accessible-premise retrieval plus hard
  negatives improves prover performance. For AI-Statistician, this means
  successful and failed proof attempts should become premise-selection training
  rows, not just trace logs.
- Loogle supports Lean/Mathlib search by constants, name substrings,
  subexpressions, and main-conclusion shape. For AI-Statistician, this supports
  a future provider that converts theorem goals into type/conclusion-shape
  probes and records the external evidence separately from local proof evidence.
- LeanSearch is a natural-language Mathlib search provider. For
  AI-Statistician, it is useful as an online semantic fallback, but it should be
  gated by local benchmark evidence before becoming a default provider.
- LeanExplore combines semantic embeddings, lexical BM25+, and PageRank-style
  structural importance across Lean declarations. For AI-Statistician, this
  suggests the next local architecture layer: add semantic/query-intent recall
  benchmarks first, then add local embeddings and graph-centrality reranking if
  the benchmark exposes misses.

## Implemented Now

The formal-source retrieval benchmark now has two tiers:

- `DEFAULT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK`: the stable release gate used by
  normal audits. It covers the current local/Lean-RAG source families that the
  system is expected to retrieve reliably.
- `EXTERNAL_USER_INTENT_FORMAL_SOURCE_RETRIEVAL_BENCHMARK`: an optional
  capacity-improvement suite with broader theorem-family prompts and
  user-intent phrasing. It guides RAG work but is not a release gate until the
  provider stack demonstrates stable recall.

The optional external gold cases cover:

- FormalSLT stability-to-generalization and VC/PAC sample complexity.
- lean-rademacher Dudley entropy and McDiarmid uniform-deviation bounds.
- Lean Machine Learning UCB/regret theorem mining.
- BrownianMotion Kolmogorov-Chentsov/Hölder modification theorem shapes.
- Kolmogorov extension/projective-family theorem shapes.
- SciLean Gaussian calculus/optimization theorem shapes.

This turns the new external sources into measured RAG targets without
overclaiming current support. A focused check on 2026-06-02 with the active
SQLite/Lean-RAG provider stack retrieved the default benchmark reliably, but
missed all eight optional external-intent cases (`0/8`, Recall@8 = 0.000). That
is a concrete next-capacity target for provider fusion, query expansion, and
semantic search. The benchmark still measures retrieval only; Lean/AXLE kernel
proof remains the proof boundary.

## Next Build Targets

1. Add query-intent expansion for missing primitives:
   primitive name, theorem goal, problem class, local gap reason, and candidate
   proof-bank bridge names should all become retriever queries.
2. Add source-aware reranking:
   prefer importable/local verified declarations, penalize WIP/sorry-heavy
   retrieval-only corpora for proof-bank promotion, and keep them available for
   theorem-shape planning.
3. Add proof-state/premise feedback:
   successful proof candidates become positive premise examples; retrieved but
   unused or failed candidates become hard negatives.
4. Only after the expanded benchmark exposes semantic misses, add a local
   embedding provider or external LeanSearch/LeanExplore provider behind an
   ablation gate.

## Honesty Boundary

Retrieval hits, external search hits, and benchmark recall are premise-selection
evidence. They are not proof evidence. A theorem only becomes proof evidence
after the proof-bank/AXLE/local Lean kernel audit verifies it.
