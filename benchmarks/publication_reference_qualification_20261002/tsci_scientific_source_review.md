# TSCI Scientific Source Qualification

Checked 2026-10-02. Evaluator-side source review, not an agent task, proof
certificate or numerical experiment. Earlier reference executions remain unchanged.

## Editions and Examined Material

The final theory article is Guo, Zheng and Buhlmann, JMLR 27(198):1--67 (2026),
[official record and PDF](https://www.jmlr.org/papers/v27/24-0515.html).
Its PDF SHA-256 is
`77f7d170bcfbcd6ad3cc2cbb02d4e047898b047a81b97f9db22b4d04c5f100ed`.
It is not the older preprint edition cited at the discovery checkpoint.
Examined scopes are models/identification, estimator/selection, Theorems 1 and 3,
their B.3/B.5 arguments, variance Lemma 2 with C.5, simulation S1, and the Card
application with E.1. These are selected dependencies, not a complete audit of
all 67 pages or every invoked lemma. The exact equation pages were rendered and
read, rather than trusting extracted symbols alone.

The separate [JSS software article](https://www.jstatsoft.org/article/view/v114i07)
is Carl, Emmenegger, Buhlmann and Guo (2025), DOI `10.18637/jss.v114.i07`.
Its paper hash is
`ef38e39e3aeab082c65896ea591f32299132656e86fd51a9c8070468cd842b4e`.
The examined package is the journal's TSCI 3.0.5 archive, hash
`ba3e44efb4db449f6d7b6c26897d77d442a0c96a72d36e3dc32fe0e983b65b2b`.
The existing attachment execution does not establish reproduction of the final
theory article's simulation or application study.

## Localized Findings

1. **Written selection algorithm differs from code.** JSS Algorithm 1, page 6,
   keeps overwriting `q_comp` and has no first-hit exit. Assuming an estimate is
   not significantly different from itself, its final iteration selects `Qmax`.
   Package `R/tsci_selection.R:248--254` instead chooses the first passing row.
   This is a pseudocode discrepancy, not evidence that the package always selects
   the largest space. No source was patched.
2. **Written proof decomposition needs clarification.** JMLR B.3, page 44,
   equation (57) adds `Err1 + Err2`; `E(V)` immediately subtracts both. The
   claimed exact decomposition does not follow as written. This is a sign
   inconsistency, not a disproof of the theorem. No corrected argument has been
   qualified.
3. **Inference has additional conditions.** JMLR Theorem 1 requires R1, R2-I,
   the no-dominating-observation condition and, for its feasible interval,
   consistent estimated standard errors. Theorem 3 has further selection
   conditions and a `1-alpha-2*alpha0` coverage bound, not unconditional nominal
   coverage.

## Code and Application Scope

The final article links a different
[replication repository](https://github.com/zijguo/TSCI-Replication), observed at
`ca73f039b5666b579150921d467d245802b7e2b7`. Its actual root
[MIT notice](https://github.com/zijguo/TSCI-Replication/blob/ca73f039b5666b579150921d467d245802b7e2b7/LICENSE)
was read. This pin is an observed commit, not a recovered publication release or
environment lock. It does not license the separate JSS attachment or input data.

Read pinned `Simulation Codes/Section 5.1/Simulation-DML-S1.R`,
`Real-Data/RealData_Card_V1V2.R` and `Real-Data/TSCI-Real-MRule.R`. S1 uses
20 iterations per configured round; comments describe 25 rounds. Card similarly
uses 20 splits per round and four alternative violation-space constructions.
Complete batches and their aggregation have not been
executed or qualified. Folder numbering still refers to Section 5, so file names
alone do not map the final article's Section 6 results. The Maimonides script
requires a local CSV path not supplied by that script. This is a dependency gap,
not a finding about its statistical conclusions.

## Qualification Decision and Paper Consequences

TSCI remains a substantive candidate, not an activated publication case. It
connects assumptions, first-stage learning, bias correction, model selection
and an observational application. The source-only software example is usable
only within its existing numerical-reference scope. Full-paper reproduction,
theory gold, data rights and final-study result mappings are not qualified.

Keep distinct future deliverables: faithful reproduction of a specified version;
assessment of an independently authored argument; and evaluation of collaboration
on a task that actually uses specialist feedback. A source-only run cannot
answer the third question. Matching a published estimate cannot establish its
causal truth. Diagnostics can reveal a problem without proving the remaining
assumptions. A valid alternative argument or an honest unresolved gap must not
be rejected just because it differs from a published display.

This decision does not add a product prompt, task-family rule, proof repair,
new model draw or regraded outcome. Any future task must fix its access condition,
scientific endpoint and independent authority before calls. The review stays
outside blinded author context and product RAG. Do not hold ordinary code
replication behind a claim that every upstream theorem has been proved; instead
state exactly which scientific claims that replication can and cannot assess.
