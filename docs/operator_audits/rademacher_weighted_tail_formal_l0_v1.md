# Weighted Rademacher Formal Evaluation

## Immutable Outcome

- Task: `rademacher_weighted_sum_tail_formal_known_result`.
- Benchmark: `research-l0-rademacher-weighted-tail-formal-20260909-v1`.
- Scope: standalone formal-only known result, not numbered Task115 or research E2E.
- Product/activation commit: `0b2785ff31119168e9006c7f32738c1de91c2139`.
- Run: `runs/main_worker_research_l0_rademacher_weighted_tail_formal_20260909_v1_codex_workspace_exact_haiku`.
- Sole draw: exit 1, `BLOCKED`, 237.745 seconds, gold 0/1.
- Exact target kernel closure: absent. No capability credit is added.

The single invocation and post-runtime assessment are consumed. Do not resume,
rerun, repair, rescore, or expose hidden findings to this candidate. The public
[preactivation ledger](../evaluation_activations/rademacher_weighted_tail_formal_preactivation.json)
remains the historical pre-result record. Original numbered tasks and the previous
standalone source-reproduction result are unchanged.

## Frozen Authority

The public contract fixed the concrete canonical iid sign law, arbitrary finite
index set and real weights, both sub-Gaussian and right-tail conclusions, exact
declaration prefix, and active Lean/StatInference/Statlib/Mathlib identities.
It did not assume the desired conclusion or provide the proof. Library reuse was
allowed; this was not a rediscovery or novelty benchmark.

Before the product call, the hidden positive proof passed the existing exact
declaration and axiom check. Four controls were rejected: `sorry`, a custom axiom,
a weakened conclusion, and an added hypothesis equal to the desired conclusion.
Calibration passed 5/5 without model calls. Hidden proof and controls stayed outside
Git, model workspaces, and RAG. The formal contract and full-task gold descriptor
were validated, committed, and pushed before launch.

## Observed Execution

The retained Formalizer made 44 successful Anthropic Haiku turns and 52 tool calls:
17 source searches, 4 declaration inspections, 26 scratch checks, 1 current-source
read, 1 proof-search request, 1 source submission, and 1 formal-gap report.
The workspace stopped voluntarily at a gap before its 48-turn ceiling; it was not
interrupted or restarted. Local Lean/LSP was exercised. Its admitted target was
correctly rejected as proof because the transitive axiom audit found `sorryAx`.

There was then one Critic request, rejected by the provider with `BadRequestError`
before a model judgment. Thus there were 45 attempted product turns, not 45
successful responses. All requests used `claude-haiku-4-5-20251001`. No independent
whole-target semantic review or kernel promotion occurred, and the single
post-runtime gold assessment used no model calls. The outer graph had three steps,
no Architect calls, and no workspace resumption.

The Formalizer's usage record reports 6,633 output tokens, 931 uncached input tokens,
60,746 cache-creation tokens, and 1,536,221 cache-read tokens. These are provider
usage categories, not a unique-context size or a dollar estimate.

## Demonstrated Defects

The model reported missing independent-sum and Chernoff-bound APIs. Those lemmas
exist in the frozen Mathlib source; the qualified reference proves the target in
the same environment. This is not evidence that the mathematical foundation lacks
the result.

Every explicit search requested 8 results, but the runtime applied the proactive
prompt compactor, whose unscoped policy retained only one hit. The returned tool
observations indeed contained one hit. A shared correction now passes the requested
count to that projection and leaves oversized explicit observations to the existing
atomic tool-loop boundary. It adds no theorem hint, ranking heuristic, corpus,
proof body, repair agent, or retry. Synthetic tests cover 1/4/8 results, long complete
signatures, retained discovery-only labels, omitted proof bodies, and the actual
runtime callback. This does not show the consumed task would now pass.

Other observed issues remain unresolved:

- Operator configuration mixed two checkouts: explicit Lean and external RAG used
  `~/.codex/external/EmpericalProcessLEAN-main`, whereas the default local index used
  the repository's `external/EmpericalProcessLEAN-main`. Both have commit `4cec7860`,
  but the exact-source resolver requires files inside the selected project.
  The CLI's additional external-provider flag does not relocate its default local
  source roots. This is an operator/setup confound, not evidence of insufficient
  Haiku mathematics. Future runs must align the canonical project and source roots;
  do not bypass the source boundary or rerun this task to erase the failure.
- Search metadata also included malformed module paths such as `Mathlib.Moments.SubGaussian`
  and filesystem paths rendered as Lean modules. An exact inspection of
  `ProbabilityTheory.HasSubgaussianMGF` returned `ACTIVE_PROJECT_DECLARATION_NOT_FOUND`
  despite the declaration being in the active dependency, consistent with the root
  mismatch above. Module-name derivation still needs a generic synthetic test,
  not a declaration-specific alias or an assumption that switching paths fixes all
  retrieval problems.
- The selected OpenProver request was rejected before search because
  `target_theorem_statement` and `target_lean_declaration` were missing. It supplies
  no evidence of a live HLM proving call.
- The Critic record preserves only the exception class, not the provider's reason.
  Its `BadRequestError` cause is unknown; do not label it authentication, context
  overflow, schema failure, or mathematical rejection without further evidence.

## Verification And Scope

Before the draw, the existing formal/semantic/workspace panel passed 100/100 in
221.14 seconds. After the shared search correction, the source-index/topology/scoped
panel passed 65/65 and the synthetic runtime callback passed 1/1. The full suite
passed 1286/1286 in 393.35 seconds. Shared fix commit:
`38a18b0bd8b3d774c8370e83f537c9d31911439a`. No consumed evaluation was used as a
regression fixture or invoked again. A scan of 51 run artifacts found no credential
patterns or hidden evaluator paths/proof hash outside the operator launch record;
this checks explicit leakage markers, not arbitrary semantic contamination.

The research-first goal is still active and unmet. This draw completes a separate
measurement in the existing evaluation order; it does not establish Theory,
scientific Python/R, confirmatory simulation, or research-E2E acceptance.

## Immutable Hashes

- Runtime manifest: `58e27718087169b687eb723e1ac9ecd5bf33ce037fce951a97d2231cad6efe94`.
- Runtime result: `1c05f4aabd7175e0fb37da72eaf75276ac5cacb67b07ef97d2d6f1f54d624c61`.
- Gold assessment: `abe3871c643175b9fe4ff26a1dd400243f7a781f3e605871d0355609b8c85e99`.
- Progress trace: `5eb5009b0d9981f24d3d44f87a98cb4dec3b01b46ce0c8b401cd9f324b62ae76`.
- Launch: `40a5f256bf36a1f82415cb2258c3d34023e018673114dbacbab8796082ccf36a`.
- Terminal: `b9ef49e9bf89ce7db5861ae8783ad3013d739d3d0237d192b0ba41b61f90c804`.
- Failure summary: `6160bc26b8394ec36a8aa6ff39380a41d59c47b9e23985ed080879279e12f50d`.
