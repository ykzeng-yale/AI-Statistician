# Complete-randomization Neyman L0 v1 operator audit

## Frozen authority

- Task: `complete_randomization_neyman_variance_known_result`
- Family: `finite_population_randomization_inference`
- Public reference: Jerzy Splawa-Neyman, *On the Application of Probability
  Theory to Agricultural Experiments. Essay on Principles. Section 9*,
  Statistical Science 5(4), 1990, DOI `10.1214/ss/1177012031`
- Visible question SHA-256:
  `1bb76d752a3b6109f5290432b222a6a61840640de7a687dbd04344319dd79eb1`
- Visible question hash:
  `c55aba7eb290e4b43e692f9e5977e000c0e33d237f54f0396ae9a91e20b505d4`
- Evaluator descriptor:
  `4dfb3bd9a11f4d81881286301cb35e05c0befb575aaa98322eee8518c19fa749`
- Activation commit: `7db5330283f32cf4f296b3615568ac3de16b23d9`
- Runtime code head: `0ef27a25e97d24965d6df9d60a4ee46b3f0ea43d`
- Model for every enabled live role: `claude-haiku-4-5-20251001`
- Formal evidence: `not_applicable`

The public task and evaluator-only gold were calibrated, frozen, committed,
and pushed before the first product-model call. The task received exactly one
fresh model draw and one post-termination hidden evaluation. Its immutable
full-task score is `0/1`; it must not be rerun, resumed, repaired, or rescored.

## Runtime result

The canonical runtime terminated `BLOCKED` after seven outer iterations. It
recorded six handoffs, one executed generated algorithm, no generated
simulation, and failure classification
`architect_metric_protocol_source_workspace_exhausted`. Research evaluation
was `0/1`, although the run was mode-conformant and correctly kept Formalizer
inactive under task intent.

TheoryDeveloper used one persistent Markdown/LaTeX workspace for 13 model
turns and 13 model-selected tools. It wrote two documents, ran two Python
scratch checks, and explicitly committed a checkpoint. The independent
preflight referee used another isolated ten-turn workspace, read the exact
documents, ran three scratch checks, wrote a Markdown report, and accepted the
handoff for exploratory coding.

AlgorithmEngineer remained in one five-turn source-owning session. Its first
Python submission failed because `run_sandbox` did not accept the runtime ABI;
the raw traceback returned to the same model. One subsequent tool input was
truncated before execution, was reported as an ordinary observation, and the
same session continued. The final source executed and was explicitly
committed. The isolated generated-code reviewer first submitted an invalid
terminal envelope, received the exact validation error in the same session,
and then submitted an accepted envelope. There was no subsystem replay,
Architect repair route, source patch, or second scheduler.

The metric author produced a candidate and the independent reviewer found two
high-severity threshold/measurement contradictions. The same author received
those exact findings and regenerated the full structured packet once, but
changed rationale while retaining both rejected numeric gate values. The
reviewer failed closed before confirmatory execution. This is correct evidence
behavior. At runtime head `0ef27a25`, it localized the then-remaining harness
mismatch: metric authoring still used detached full-packet JSON regeneration.

## Hidden evaluation

The immutable hidden result is `0/1`:

- algorithm acceptance checks: `13/15`;
- exact empirical checks: `8/8` over 70 estimator invocations;
- generated simulation: not reached;
- runtime unresolved-gap disclosure: absent because the graph blocked early;
- formalization: `not_applicable`.

The estimator's numerical formulas passed every hidden exact-enumeration check.
The two algorithm failures were public-interface violations. The source reads
inputs through `request.get`, so an extra request key is accepted, and it
coerces outcomes with `float(y)`, so values such as numeric strings and booleans
can be accepted. The public ABI explicitly declared a closed request object and
forbade coercion. The generated-code reviewer therefore false-accepted an exact
visible-contract defect. Future work must improve model-owned source testing
and adversarial review; it must not encode these two cases as runtime patches.

## Theory false positive

The final theorem statements and the exact-enumeration scratch results are
correct, but the authoritative derivation contains false load-bearing algebra:

1. `theory_derivation_complete_randomization_neyman.md:127-133` uses
   `(N-n)/(N-1) * S^2/n` while defining finite-population variance with divisor
   `N-1`. Under that normalization the correction is `(N-n)/N * S^2/n`.
2. Lines 175-195 assemble those incorrect terms; in particular line 185 is not
   algebraically equal to its left-hand side. The document jumps from false
   intermediates to the correct final Neyman variance.
3. Lines 273-307 continue the wrong finite-population correction, explicitly
   abandon the calculation, and appeal to a standard sample-variance result
   without completing the promised derivation.

The independent report nevertheless labels the wrong sampling formula and
final assembly correct at `review-49353a808429e63c5f3f.md:55-76`. It notices
the abandoned sample-variance derivation at lines 91-106 but still accepts the
packet for exploratory execution. The frozen hidden semantic judge also
returned nine satisfied claims after a `12/12` calibration.

This is not a missing checklist or parser rule. Both existing prompts already
instruct the reviewers to reconstruct decisive equations, inspect intermediate
steps, and refuse to let a correct final statement cancel false derivation.
The exact-Haiku reviewers made the same mathematical false positive. Automated
theory-pass fields are therefore retained as protocol facts but receive no
operator capability credit for this task.

## Shared conclusion

The Codex-derived lifecycle worked where it was actually used: one model-owned
session selected tools, observed raw failures, revised its own artifact, and
committed exact external state; an invalid terminal tool call stayed in the
same reviewer turn; provider-local recovery did not replay a subsystem.

Post-consumption commit `e7d0174a` implemented the shared metric correction as
one persistent source-owner loop with parent-hash-bound complete submissions,
direct validator feedback, and isolated review. It added no repair agent,
formula detector, scheduler, or score change and is future-task regression
evidence only. Post-consumption commit `b9ece439` then required the existing
isolated referee to persist an independent pre-candidate reconstruction and a
distinct post-inspection comparison under exact hashes. That change adds no
agent, call, formula, or mathematical validator and also has regression evidence
only. It must be evaluated on a future disjoint frozen task while provisional
theory may still open exploratory coding. Nothing can alter this consumed result.
