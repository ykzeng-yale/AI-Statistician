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

The release-style `research-system-audit` also records a
`proof_search_retrieval_no_registered_ablation` diagnostic. It disables
registered proof-bank bodies so dependency-graph RAG lift is visible as
candidate-frontier/search evidence instead of being hidden by gold proof-bank
shortcuts. Those rows remain retrieval/search evidence unless AXLE or local
Lean kernel verification is enabled for the proof-search run.

The audit now also exports `formal_verifier_queue` after the
`formalization_delta_plan`. This queue joins theorem-level formalization
routes, the no-registered proof-search RAG candidate delta, and selected
kernel-smoke context into owner-agent work items for the FormalVerifier. The
queue now also attaches related proof-bank obligations, prior proof-attempt
positives/negatives, proof-search solved subclaim history, graph-neighborhood
dependency depth, source-trust class, semantic-faithfulness status, and
kernel-smoke overlap calibration for related subclaims. It is useful for
choosing the next theorem/bridge proof attempt, but it is still a task contract
rather than proof evidence.

The audit now also exports `formal_verifier_replay` from that queue. Replay
tasks choose concrete next modes such as kernel-calibrated subclaim replay,
proof-search subclaim replay, bridge-lemma replay, semantic route review, and
theorem-composition replay. The export also writes replay-policy training
examples, so future verifier controllers can learn from queue state, proof
history, source-trust calibration, and semantic review fields. These rows are
still executable task contracts only; they do not prove the target theorem
unless AXLE or local Lean verifies the replayed theorem/bridge proof.

## Next Build Targets

1. Expand library-aware minimal formalization planning:
   the current `formalization-delta-plan` ranks proof-bank actions by reuse,
   blocker, source-coverage, and bridge/wrapper cost, and exports a dependency
   graph linking problem classes, theorem goals, concrete Lean theorem
   skeletons, informal proof steps, imports, gaps, primitives, actions, stages,
   expected premises, verified bridge candidates, and candidate Lean
   declarations. The graph now exposes a route from target theorem to Lean
   skeleton to informal proof steps to primitives/actions, and the planner
   emits theorem-level route summaries with required primitives, reuse
   candidates, route class, and first next actions. `formal-verifier-queue`
   already turns those route summaries into ranked verifier work items with
   RAG-lift context, proof-attempt history, proof-search subclaim history, and
   explicit proof gates, plus dependency depth, import-cone size, source trust
   level, semantic-faithfulness review, and kernel-smoke source-trust
   calibration. `formal-verifier-replay-export` now turns those rows into
   route-level replay tasks and replay-policy examples. The next version should
   run those replay tasks against full theorem/bridge proof attempts and
   calibrate the queue/replay policy against the resulting Lean errors.
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

```bash
python3 -m ai_statistician.cli formal-verifier-replay-export \
  --formal-verifier-queue-dir runs/current/formal_verifier_queue \
  --out runs/current/formal_verifier_replay
```

This converts the ranked queue into replay tasks and replay-policy examples.
It is the handoff to a full theorem/bridge proof attempt, not evidence that the
attempt has succeeded.

## Honesty Boundary

Retrieval hits, external search hits, and benchmark recall are premise-selection
evidence. They are not proof evidence. A theorem only becomes proof evidence
after the proof-bank/AXLE/local Lean kernel audit verifies it.
