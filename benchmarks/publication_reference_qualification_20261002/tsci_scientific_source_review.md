# TSCI Scientific Source Qualification

Checked 2026-10-02; source-input follow-up 2026-10-03. Evaluator-side source review, not an agent task, proof
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

### Paper-to-Code Mapping Follow-up

The complete recursive tree at the same pin was inspected (`truncated=false`),
along with the S1 and B1 aggregation scripts. This is static source inspection,
not a new execution or replacement for the earlier attachment result.

| Intended material | Actual source scope and unresolved issue |
| --- | --- |
| Section 6.1, S1 component of Figure 2 | `Simulation Codes/Section 5.1/Simulation-DML-S1.R` and its `read-` script form the producer/aggregator pair. The producer requests `Source-DML_helpers.R`, absent from the inspected tree. Its default `a=2.1` is outside the aggregator's `0.6:2.0` grid. A single unchanged invocation would not reproduce that figure. |
| Section 6.2, B1, Table 1 and supplemental Table 8 | The B1 producer and coverage/bias/length readers enumerate batches and settings. The producer requests `Source-otherRF-hetero.R`, also absent from the tree. Oracle RF comparators are distinguished from data-selected TSCI; their access advantage must remain explicit. |
| Section 7 versus Appendix E.1 | `RealData_Card_V1V2.R` writes four alternative-basis split results relevant to E.1. This does not by itself produce the main application figure or its multi-split interval. Full main-case aggregation remains unqualified. |

The reference-paper mappings are Section 6.1/Figure 2, Section 6.2/Table 1,
Section 7/Figure 4, and Appendix E.1; the repository's older folder numbering
does not define those scopes. The documented weak/misspecified settings include
undercoverage. A faithful reproduction is not required to make every method
achieve nominal coverage, and a published undercoverage pattern is not evidence
that the reproducing agent failed. Scientific interpretation and numerical
reproduction remain separately assessed.

Theorem 1's proof route passes through Theorem 6 in B.3 and its remainder
dependencies, including Lemma 5/C.2. Feasible variance and selected-basis
inference have additional obligations. The localized sign discrepancy already
recorded above has not been resolved by this inspection or by a simulation.
Do not insert a corrected proof into gold without an independently checked argument.

### Tool-Readable Official Code Input

The 2026-10-03 follow-up cloned the full advertised official history: 32 commits,
with only `main` advertised and no tags. Neither missing helper appeared under
its exact path in that history. This does not establish that the authors never
distributed it elsewhere. An exact-filename search of this workspace and the
operator-provided `AI for Math Resources` collection also found neither file.
No source, generated result or old evaluation changed.

The existing product CLI froze all 66 commit files, preserving paths and bytes:

```sh
git clone https://github.com/zijguo/TSCI-Replication "$FRESH_CHECKOUT"
.venv/bin/ai-statistician freeze-research-source-project \
  --repository "$FRESH_CHECKOUT" \
  --revision ca73f039b5666b579150921d467d245802b7e2b7 \
  --snapshot-id tsci-jmlr-official-source-ca73f039 \
  --source-horizon 2026-10-03 \
  --repository-url https://github.com/zijguo/TSCI-Replication \
  --license MIT --out "$FRESH_SNAPSHOT"
```

The local snapshot is `runs/publication_case_assets_20261003/source_snapshot`.
Its snapshot hash is
`10e8dfdfb80b410e7228bb70e2b36d546ff73c1bc203a15eb2b22a15c6eb6cb3`;
its manifest SHA-256 is
`234876ae17e14738874b839f9f7140bd703622d4be580679bfd587bb06423922`.
An exact rebuild at another path can have different path-bound metadata; verify
the commit and file identities rather than assume its manifest bytes match.
The production snapshot loader returned no identity errors. Its actual list/read
tools listed the seven `Source Codes` entries and read the B1 producer's first
four lines unchanged. This was tool access, with zero model calls and no R run;
it is not autonomous reproduction or a qualified execution environment.

| Input | SHA-256 |
| --- | --- |
| `Simulation Codes/Section 5.2&D.4&D.5/Simulation-TSCI-invalidIV-B1.R` | `fbc3a89d638231521aeb5016692c355e4ff6e493c440242ca4dd48773de3fef0` |
| `Real-Data/RealData_Card_V1V2.R` | `9e1415d29b7cdaaab78f9fe9e0644c13888b3d03c8f72bedfb7dd6233b95411b` |
| `Source Codes/Source-RF-hetero2.R` | `f148d6dea810a674aabced3b56b15f35f560d57a76be023bb969844b63f7840c` |

B1's reader grid has 18 settings and 25 rounds, requiring 450 batch files and
500 Monte Carlo observations per setting when every 20-observation batch is
complete. These are source-declared counts, not executed or successful results.
The producer fixes one setting and round in its source; running it once is not
the full grid. Its heteroskedastic comparator functions are not supplied by the
available homoskedastic helper. Card's four alternative bases likewise remain
the E.1 scope, not the main-case multi-split analysis. Paper text, input data,
environment locks, complete execution/aggregation, scientific tolerances and
mathematical assessment are still separate unresolved inputs. The frozen code
can be supplied through the existing `source_snapshot_ref`; this evaluator-side
review and reference outputs must not be included as author hints.

## Qualification Decision and Paper Consequences

TSCI remains a substantive candidate, not an activated publication case. It
connects assumptions, first-stage learning, bias correction, model selection
and an observational application. The source-only software example is usable
only within its existing numerical-reference scope. Full-paper reproduction,
theory gold, data rights and final-study result mappings are not qualified.

Keep this one source family while finishing qualification; do not replace it
with another easy numerical panel. The proposed bounded illustration is a
published-method comparison under invalid instruments (B1), paired with the Card
application and assumption-qualified mathematical explanation. It is not a
request to rediscover the entire article or establish every asymptotic theorem.
Access to paper, author code and data defines replication, not blind discovery.
The final accessible assets, executable reference, mathematical claims/authority,
aggregation and acceptance rules still need prospective qualification before
this scope becomes a frozen task. Missing helpers are explicit source gaps;
do not silently substitute a different script, package or repaired implementation
and call it unchanged replication. Optional Lean is not a gate on this non-formal
illustration.

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
