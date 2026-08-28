# Task 74 operator audit: JSS sandwich R source replication

## Immutable scope

Task `sandwich_jss_2004_r_public_replication` consumed exactly one product draw at
code head `9feec25d9f4c819ba4bbd991bd1c8469b9d7f4c8` and exactly one post-runtime
hidden evaluation. The product used `claude-haiku-4-5-20251001` for every enabled
role. No Sonnet or Opus call, model escalation, runtime feedback from hidden
authority, source mutation, product-draw rerun, source repair, resume, rescore, or
resampling occurred.

The initial Architect stage did make two model calls. Its first structured packet
incorrectly included simulation targets even though empirical evidence was not
applicable; validation rejected it and the legacy structured-output helper regenerated
the complete packet once. The accepted packet then routed correctly. This was not a
source retry or second scheduler, but it is unnecessary control-plane regeneration
and remains a mismatch with the desired small Codex-style action loop.

The runtime directory is
`runs/main_worker_research_l1_sandwich_jss_r_replication_20260828_v1_codex_hash_bound_r_exact_haiku`.
The runtime ended `ACCEPTED` after three outer graph steps. The automated hidden
evaluation returned `1/1`: the exact-source harness passed all 12 checks and the
calibrated exact-Haiku report judge marked all ten semantic obligations
`SATISFIED`.

## Evidence that is valid

The source-execution component is real and useful evidence:

- The unmodified official `v11i10.R` source was executed once under the pinned R
  4.4.3 environment with return code 0 and no network access.
- Source, entrypoint, interpreter, environment, stdout, stderr, and declared output
  identities matched the frozen authority.
- Standard output hash is
  `00a4fb91848c84921fa545d36c73a51e994e88515ad249609a5e8bce9f8f07cb`;
  standard error hash is
  `48c3935d9c7cecc6fe70cbcdc91ebd3f9f163a2e211bf98b32b7292b98e89c16`.
- The source owner used one persistent model-tool-observation session: eight model
  turns and eleven model-selected tools, including source search/read, the pinned R
  run, raw result inspection, Markdown writing, and checkpoint commit.
- A rejected attempt to read binary `Rplots.pdf` as UTF-8 returned a raw tool error
  to the same source owner. The model continued without an Architect route, repair
  worker, fallback, or second scheduler.
- Formalization was correctly not applicable and did not run.

This validates the Codex-shaped harness lifecycle and the generic hash-bound R
execution mechanism. It does not validate every scientific claim in the report.

## Operator-invalidating findings

The 437-line model-authored report contains a material inference error and several
unsupported interpretations:

1. At line 146 it calls `p = 0.05586` "marginally significant at the 0.05 level";
   line 353 repeats that the term is marginally significant. Since
   `0.05586 > 0.05`, the conventional 5% test does not reject. Proximity to the
   threshold can be described, but not as significance at that level.
2. Line 119 says larger HC0 standard errors indicate heteroskedasticity and describes
   HC0-to-HC4 as increasing robustness. A difference in standard errors is not a
   heteroskedasticity test, and these estimators do not form a universal ordered
   robustness scale.
3. Line 217 infers that the supF test is "more powerful" from one pair of observed
   p-values. Power is a repeated-sampling property under alternatives and cannot be
   established by this execution.
4. Lines 245 and 365 attach the estimated breaks to oil-crisis, stagflation, and
   Volcker narratives and call that alignment robust. Those historical explanations
   were not evaluated by the source run and should have been labeled speculative.
5. Lines 296 and 402 call the PDF's logical visual content reproducible even though
   lines 404 and 416 correctly admit that visual content was not inspected. The
   product had artifact metadata and source-derived plot expectations, not visual
   verification.

The runtime Critic read the report and raw evidence but returned `ACCEPT`. The hidden
judge also returned ten of ten `SATISFIED`. Their false acceptance shows that a
qualified closed obligation list plus one long-form negative control does not ensure
open-ended detection of extra incorrect claims in a new report.

Separately, the Architect packet duplicated frozen task-intent fields and needed one
full-packet regeneration before the source workspace began. Future shared design
should reduce Architect output to planning decisions and one next action while
runtime retains frozen evidence requirements; it should not add another repair
worker or task-specific exception. This consumed task is not rerun to validate that
future simplification.

## Disposition

The immutable automated result remains recorded as `1/1`; it is not rewritten.
Trustworthy full-task capability credit is `0/1`, so aggregate credit remains
`4/74`. The exact source execution remains component evidence, while the report,
runtime Critic verdict, and hidden semantic verdict are not accepted as a reliable
scientific interpretation.

No product or evaluator change is made from this consumed output. The appropriate
system conclusion is a capability boundary: the general Codex-style action harness
worked, while exact Haiku author/referee semantics were insufficient. Production may
use Sonnet, but all frozen tests and evaluations remain exact Haiku and Opus remains
prohibited. Future evaluations must continue to allow operator invalidation rather
than adding task formulas, prose parsers, deterministic claim repair, retries, extra
agents, or model escalation.

Recording verification passed the research ladder `72/72` and the complete repository
`997/997` in 82.49 seconds. Compileall, JSON, diff hygiene, secret scanning, and the
unchanged production architecture budget passed at 149,991 lines. No post-run product
or hidden evaluator model call occurred.

## Immutable hashes

- Runtime manifest:
  `7c62c9e668a709e977190e0f7f3cf1a54f16859690d612edd001a86e13b9792c`
- Runtime result:
  `682edc9c92a598da45f3de3da0114ac85dc5d21428c5434649be54a153b0c46a`
- Hidden evaluation:
  `8962c540bfc4036ee28408bfe962aebdf967869b5280b28e7e25eb47b9dd9406`
- Runtime completion summary:
  `7546fc4e449dc2fadf71b86f6c5f26c9f1833ecf4e9018916c227f3b5c765cea`
- Runtime failure summary:
  `24cb04a35027713ddc327549df51ae6eeb6939955b1649c1b2c05b34e73c0ac6`
- Runtime LLM topology:
  `e0d8e0c8f0fdbfef722237ee1c8271850bcefe639f69c6744d8496ee6eb9b95c`
- Model-authored report:
  `73d555669b3bbc2eb818b2c8b4c57d3a784235361e998a9b6eb33443880aecb7`
- Source replication manifest file:
  `7f592d9d5cdb37811969c596f6d0c51523e63899815386a0e49bacbea0bf1151`
