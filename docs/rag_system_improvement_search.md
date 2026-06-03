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
overclaiming proof support. A focused check on 2026-06-02 with the active
SQLite/Lean-RAG provider stack retrieved both benchmark tiers:

- Default release suite: `6/6`, Recall@8 = 1.000, MRR = 0.889.
- Optional external-intent suite: `8/8`, Recall@8 = 1.000, MRR = 0.844.
- Combined suite: `14/14`, Recall@8 = 1.000, MRR = 0.863.

The benchmark still measures retrieval only; Lean/AXLE kernel proof remains the
proof boundary. The immediate `0/8` failure mode found during integration was a
stale SQLite cache that predated the newly registered external Lean roots, not a
semantic-ranking failure. The cache path now checks that every existing
configured Lean root is represented by source id and rebuilds when the cache is
stale. The next-capacity target is therefore not "make these eight
retrievable"; it is to keep this recall stable while adding source-aware
reranking, proof-state feedback, and harder semantic/paraphrase queries.

The shared `EmpericalProcessLEAN/lean_rag` package was rechecked against branch
`codex/rag-infra-package` at commit `9f0e0ad1277a`. Its useful new surface is
package-level refresh discipline, not a generated index to vendor:

- `shared_proof_retrieval.py status` records saved checkout state and live drift
  signals, including dirty checkouts and upstream ahead/behind state.
- `refresh_lean_reuse_sources.py --rebuild-index` refuses to rebuild
  `statinference-local` records from dirty `StatInference` paths unless the
  explicit dirty override is used.
- `knowledgebase/source_registry.json` carries the trust policy:
  external sources are candidate/documentation search only, candidates must be
  verified with Lean, and dirty proof checkouts should not be refreshed.
- `knowledgebase/seed_queries.jsonl` packages reusable retrieval recipes for the
  active Durrett, Chewi, and Vaart proof lanes.

AI-Statistician now has `ai-statistician lean-rag-package-audit`, and the
release-style `research-system-audit` records the same package contract through
`lean_rag_package_*` counts and artifacts. This lets the four-hour monitor and
other proof chats see whether the strongest shared RAG package is present,
fresh enough to trust as retrieval infrastructure, and still respecting the
Lean proof boundary.

## Next Build Targets

1. Add library-aware minimal formalization planning:
   the current `formalization-delta-plan` ranks proof-bank actions by reuse,
   blocker, source-coverage, and bridge/wrapper cost, and exports a dependency
   graph linking problem classes, theorem goals, concrete Lean theorem
   skeletons, informal proof steps, imports, gaps, primitives, actions, stages,
   expected premises, verified bridge candidates, and candidate Lean
   declarations. The graph now exposes a route from target theorem to Lean
   skeleton to informal proof steps to primitives/actions. The next version
   should add dependency depth, import-cone size, source trust level, proof
   attempt history, and semantic-faithfulness review.
2. Add query-intent expansion for missing primitives:
   primitive name, theorem goal, problem class, local gap reason, and candidate
   proof-bank bridge names should all become retriever queries.
3. Add source-aware reranking:
   prefer importable/local verified declarations, penalize WIP/sorry-heavy
   retrieval-only corpora for proof-bank promotion, and keep them available for
   theorem-shape planning.
4. Add proof-state/premise feedback:
   successful proof candidates become positive premise examples; retrieved but
   unused or failed candidates become hard negatives.
5. Only after the expanded benchmark exposes semantic misses, add a local
   embedding provider or external LeanSearch/LeanExplore provider behind an
   ablation gate.

## Library-Aware Delta Planning

The next prover/formal-verifier bottleneck is not only "which premise proves the
current goal?" It is "what is the smallest useful Lean extension Δ that turns
the current library into one capable of proving the target theorem?" The current
system now exposes a lightweight version:

```bash
python3 -m ai_statistician.cli formalization-delta-plan \
  --proof-bank-actions-dir runs/current/proof_bank_actions \
  --primitive-source-coverage-dir runs/current/primitive_source_coverage \
  --out runs/current/formalization_delta_plan
```

This outputs exact-reuse rows, bridge-chain composition rows, assumption
interfaces, minimal wrappers, bridge lemmas, and first-principles primitive rows
with heuristic costs, plus `formalization_delta_graph.json`. The graph is
planning evidence only. It should eventually be upgraded with dependency depth,
import-cone size, source trust level, proof attempt history, theorem-goal nodes,
informal-proof-step nodes, and semantic-faithfulness review.

## Honesty Boundary

Retrieval hits, external search hits, and benchmark recall are premise-selection
evidence. They are not proof evidence. A theorem only becomes proof evidence
after the proof-bank/AXLE/local Lean kernel audit verifies it.
