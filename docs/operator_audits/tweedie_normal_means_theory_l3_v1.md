# Task106 Operator Audit: Gaussian Normal-Means Tweedie Identities

## Disposition

`OPERATOR_INVALID` after one consumed product draw and one consumed hidden assessment.

The canonical runtime accepted the task and the frozen hidden evaluator reported a full automated pass: seven of seven structural checks and eight of eight semantic claims. Those results remain valid records of what the configured harness judged. They do not receive trusted capability credit because the authoritative document contains active false statements that both the runtime referee and the two-pass hidden semantic judge missed.

Task106 is immutable. This audit did not edit the candidate, generate runtime feedback, request a revision, rerun the product, repeat hidden assessment, rescore with a changed rubric, or switch models.

## Correct Core

The document eventually obtains the requested posterior-mean, posterior-variance, normal-prior, integrated-risk, and information-bound formulas with the correct final signs and scales. It also keeps formalization, code, simulation, source replication, and novelty out of a theory-only task. This is meaningful subsystem progress, but it is not enough for full-task credit when active explanatory claims are false.

## Blocking Findings

1. **The arbitrary-prior posterior is written with an invalid measure/density hybrid.**

   At lines 17-18 the document calls `phi_sigma(y-theta) G(d theta) / f(y)` a density with respect to `G`; the Radon-Nikodym density with respect to `G` is `phi_sigma(y-theta) / f(y)`, while the displayed expression is posterior measure notation. Lines 40-41 and 55 then integrate this alleged `G`-density against Lebesgue `d theta`. The later `G(d theta)` ratio is correct, but the active setup directly conflicts with the frozen requirement to handle a prior measure without assuming a Lebesgue density.

2. **The information-bound explanation adds a false variance and Cramer-Rao argument.**

   Lines 339-340 correctly infer `I(f) <= 1/sigma^2` from nonnegative Bayes risk. Line 342 then claims the posterior mean has variance at most `sigma^2` and presents that as a Cramer-Rao derivation. For the document's own normal-prior check,

   `Var(E[Theta | Y]) = tau^4 / (tau^2 + sigma^2)`,

   which exceeds `sigma^2` for sufficiently large `tau^2`. The posterior mean is also not the unbiased location estimator invoked by that paragraph. The correct risk identity does not rescue this additional active explanation.

3. **The empirical-Bayes dependence explanation invokes a nonexistent independence premise.**

   Line 366 says reuse of data violates an independence assumption in the law of total expectation. That law has no such assumption. Data reuse and selection do require separate empirical-process analysis, as the visible task requests, but the stated reason is mathematically false.

4. **The regularity-gap section mischaracterizes Gaussian convolution.**

   Lines 399-405 suggest first/second differentiation and posterior moments require tail conditions or a finite second moment of `G`, and that `f` or `f'` may fail to vanish for a heavy-tailed probability prior. For each fixed `y`, the relevant polynomial-times-Gaussian kernels are bounded and integrable against every probability measure; Gaussian convolution and its derivative are continuous and vanish at infinity. These are not the genuine unresolved gaps claimed by the document.

5. **The authoritative artifact retains abandoned false algebra as active prose.**

   Lines 59-100 retain a wrong derivative sign before correcting it, and lines 200-215 retain a substitution that confuses `f''/f` with `ell''` before repairing it. The prompt explicitly states that every unmarked claim is active and only material marked `REJECTED` or `SCRATCH` is nonauthoritative. A persistent theory workspace should keep exploration in scratch artifacts and commit a coherent mathematical document.

## Reviewer Failure

The exact frozen 2,822-character objective reached the referee, so Task105's truncation bug was genuinely fixed. However, the 129-line referee report still opens with a summary, proceeds section by section, adds praise and checkmarks, and reports no blockers despite protocol v44 asking for findings first and forbidding that filler. It notices the retained sign error but treats correction later in the document as sufficient, misses all four conceptual defects above, and repeats the faulty claim that the information bound is a Cramer-Rao consequence.

The hidden protocol-v11 judge likewise marked all eight claims satisfied. Its rubric explicitly covered arbitrary-measure notation, correct information-bound reasoning, dependence/selection scope, and genuine regularity gaps. This is therefore an evaluator false positive, not a missing hidden requirement.

## Harness Implication

The exact-context Codex principle was necessary but not sufficient. Future shared improvement should remain model-owned and content-neutral:

- authoritative Theory checkpoints should present polished active mathematics, with abandoned attempts moved to scratch or explicitly marked rejected;
- referee and semantic-judge prompts should treat any contradictory active assertion as a violation even when a correct endpoint also appears;
- adversarial review should search the complete document for counterexamples to explanatory claims, measure notation, assumptions, and scope, not only locate positive excerpts for rubric endpoints;
- acceptance must remain findings based and isolated, with raw observations returned only to the current source owner on a future unconsumed task.

No Tweedie formula, Gaussian-mixture rule, symbolic parser, task-specific validator, repair worker, retry, fallback, scheduler, mandatory Lean lane, Sonnet call, or Opus call should be added.

## Immutable Evidence

- Product code head: `42f0334622f3eba49f1d2f5645fe3bff00cd6b43`
- Product model: `claude-haiku-4-5-20251001`
- Runtime: 33 client-tool model turns, 39 tool executions, 2 raw tool errors, 3 outer iterations
- Authoritative document: 406 lines, SHA-256 `4851470bdd9d83d4a6a87a629faf8cfc39e487a01e73a0a029223823336c53f5`
- Referee report: 129 lines, SHA-256 `fd822483f4322e1d8246dfe5a85bb239c64f0b439d5dd9f5113b70334b77e7aa`
- Runtime manifest: SHA-256 `1e17c8ffad20ef01f8ac1722e5aaaefaef535118f73772cfc8e04ae20c6d0cb2`
- Hidden assessment: SHA-256 `d2df393400f54c3508d57eebcee965b2c7dd3dbe938d10f5c2269f8adbff7b95`
- Hidden assessment model calls: 2
- Runtime feedback from hidden authority: false
- Automated full-task result: pass
- Trusted full-task result: fail
