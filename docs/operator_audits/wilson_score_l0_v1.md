# Wilson Score L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku run is **failed and closed**. TheoryDeveloper wrote and
checkpointed a source-grounded Markdown/LaTeX theory workspace, but independent
pre-execution review exhausted its existing tool loop without producing a valid
review packet. No algorithm, simulation, Critic, hidden-gold, or Formalizer execution
followed. The task remains `0/1` and must not be rerun, manually repaired, or rescored.

Run directory:
`runs/main_worker_research_l0_wilson_score_20260814_v1_document_theory_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `217ae574810ea185e757e19a669e719d8252fa8526046b9ef6a5c664eccadfbc`
- Hidden-gold report SHA-256: `2ea5cf3ece19b5f0dc37a77f09de1f2a57da58f5120106d6c063429292155a22`
- Failure summary SHA-256: `8dbd96a837aa2a52a7e63a3209a717ec58e622d0172ad0b58a871498691d39f1`
- Theory document SHA-256: `694151df6856a881ea4ddbbf63d579577217e277790fafedbd2d3c8aa2d569b7`

Every enabled live agent used `claude-haiku-4-5-20251001`. Formalization was optional
and nonblocking by frozen task intent; no Lean work ran, so Lean was not the blocker.

## Review Transport Failure

The run completed four outer traces. In one source-owning session, TheoryDeveloper
used eleven model turns and eleven runtime-executed tools to inspect the workspace,
search and read two frozen source documents, write one 347-line, 13,964-byte theory
document, inspect its final hash, and explicitly commit a checkpoint.

The independent reviewer then read the complete theory document, inspected task-bound
sources, and attempted two substantive `submit_theory_preflight_review` calls. Both
were rejected because the provider returned no usable rows for the required sixteen
claim slots, six dimension slots, and one estimator slot. The old terminal interface
required the same mathematical reasoning to be repeated across a large structured
packet even though the reviewer had already developed a coherent report.

This is a harness-interface failure, not evidence that the candidate theory should
have passed. Runtime correctly withheld implementation and hidden evaluation.

## Theory Audit

The authoritative Markdown representation made the candidate directly inspectable,
but the checkpoint was not mathematically or executably ready:

1. Lines 108, 124, and 172 contain incorrect square-root rewrites, followed by
   `Wait`, `Hmm`, and recalculation prose. The claim index nevertheless marks all
   sixteen claims `SUPPORTED`, and `rejected_alternatives` is empty. False scratch
   algebra therefore remains inside the active authoritative derivation.
2. Lines 280-284 use `q(0) >= 0`, `q(1) >= 0`, and upward convexity to conclude that
   both roots lie in `[0,1]`. That is incomplete and partly circular: the argument
   still needs an interior nonpositive value such as `q(p_hat) <= 0`, together with
   the boundary cases, or a direct endpoint proof.
3. The estimator ABI defines
   `z = Phi^{-1}(1 - confidence_level/2)`. If `confidence_level = 1-alpha`, the
   required probability is `(1 + confidence_level)/2`; the submitted expression is
   wrong and would make a 95% interval use the 0.525 quantile rather than 0.975.
4. The ABI labels the endpoint values themselves as `O(n^-1/2)` and the center value
   as `O(n^-1)`. Those values are generally order one; only interval width and
   deviations or regularization corrections have the stated rates.
5. Lines 13-27 define the score statistic using division by `p(1-p)` while later
   admitting candidate endpoints `p=0` and `p=1`. A continuous-extension or explicit
   boundary acceptance convention is required.
6. Lines 324-334 omit the Clopper-Pearson endpoint conventions needed when `x=0` or
   `x=n`, despite claiming a definition valid for all binomial observations.

These are model-authored scientific defects. Product code must not add a Wilson
formula, quantile correction, containment proof, endpoint convention, or task-specific
validator for them.

## Shared Mechanism Response

The post-run correction is task-generic:

1. The same independent reviewer writes one coherent Markdown/LaTeX referee report
   after reading the hash-bound documents and sources. A compact tool envelope carries
   only ordered statuses, actual blockers, evidence references, and estimator gaps.
2. Runtime persists the exact report as a content-addressed Markdown artifact and
   binds every status to immutable claim, dimension, estimator, and prior-finding
   identity. It derives routing but does not author or patch mathematical content.
3. TheoryDeveloper is reminded to clean its current authoritative argument before
   checkpointing: known-false work may remain only as clearly rejected scratch and
   cannot support an active claim.

The change adds no agent, scheduler, retry, turn, budget, statistical formula, Lean
grammar rule, tactic rule, or model-tier escalation. Regression evidence cannot change
the frozen Wilson score, and no second model draw is permitted.
