# Normal Sample Variance L0 v1 Operator Audit

## Disposition

The single frozen exact-Haiku run is **operator-invalidated**. AgentRuntime reported
`ACCEPTED`, research evaluation reported `1/1`, and the frozen hidden evaluator
reported `1/1`, but those automated verdicts are false positives. This run does not
count as a fully passed task and must not be rerun or manually repaired.

Run directory:
`runs/main_worker_research_l0_normal_sample_variance_20260814_v1_document_theory_exact_haiku`

Immutable evidence hashes:

- Runtime manifest SHA-256: `69f397ff078548aa778daac9ef34c6813914cfdfbe3dff6da9f041d2a4ee8ce0`
- Hidden-gold report SHA-256: `d474552413fd56043edc55ed9addc7da3307d51bae160cde8b30225084203ddc`
- Theory document SHA-256: `474f8a8374dd30173c886ca72042519d2373814718909db7bba12ba4d71dcc2a`
- Preflight packet SHA-256: `622940e9aad7b08d558f8d9fc6577070bf29e27477f7212811980e08a36eb71c`

## Fatal Theory Error

The active proof of Theorem 5.1 states that if independent
`U ~ chi-square(n)` and `V ~ chi-square(1)`, then
`U - V ~ chi-square(n-1)`. That implication is false in general. In the candidate's
decomposition, the residual sum of squares `R` is independent of the mean component
`V`, while the total sum is `U = R + V`; therefore `U` and `V` are not independent.
The final chi-square theorem is true, but the submitted active derivation does not
prove it. The defect occurs at `theory_derivation.md:92` and propagates to the
variance derivation that cites Theorem 5.1.

Both independent model gates missed the same defect:

- Runtime preflight returned `ACCEPT` and explicitly endorsed the invalid difference
  argument.
- Hidden exact-Haiku theory-semantic evaluation returned `PASS` after its calibration
  suite had scored `10/10`.

This establishes that coarse dimension-level model review plus isolated calibration
is not a sufficient mathematical correctness authority.

## Evidence Chronology Error

Before metric authoring and the separately frozen downstream simulation lane, the
TheoryDeveloper ran a scratch simulation and inserted its outcomes into the
authoritative theory document under `Frozen Confirmatory Simulation Results`
(`theory_derivation.md:160-186`). Theory scratch execution is explicitly exploratory
and cannot become confirmatory evidence. The preflight reviewer nevertheless used the
contaminated document as support for acceptance.

The generated downstream simulation also ignored the runtime `replicates` argument and
used a source-local value of 2,000 (`generated_draft.py:34-68`). Its independent hidden
post-runtime algorithm and 36,000-call empirical checks passed, but that does not cure
the theory error or the internal evidence chronology defect.

## Shared Mechanism Response

The post-run correction is task-generic:

1. Bind one independent review slot to every non-rejected claim-index entry and derive
   acceptance from all claim, dimension, and estimator rows.
2. Review exploratory-versus-confirmatory chronology as an explicit scientific
   dimension; pre-review scratch output cannot support a frozen confirmatory claim.
3. Exclude formal-library retrieval and formal-unverified reporting when task intent
   marks formalization `not_applicable`.
4. Require generated-code semantic review to trace every declared runtime argument
   into the executed source or identify an explicit reason that it is immaterial.

No chi-square identity, Lean grammar rule, generated answer, or task-specific repair was
added to product code. The same source-owning model remains responsible for revising
its Markdown/LaTeX or executable source from raw review observations.
