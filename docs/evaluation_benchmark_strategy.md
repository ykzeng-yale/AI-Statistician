# Evaluation Benchmark Strategy

Updated: 2026-08-14

## What evaluation must separate

AI Statistician has two different evaluation authorities.

1. Product research evaluation asks whether the system produced defensible theory,
   replication, code, empirical evidence, novelty analysis, and an honest gap
   ledger for the task's frozen intent.
2. Strict formal-capability evaluation asks whether the integrated system also
   closed the exact theorem in Lean with target-bound kernel evidence.

The second is deliberately stronger, but it is not the definition of every useful
research task. A missing optional Lean proof cannot erase accepted empirical
evidence. Likewise, simulation, retrieval, or model agreement can never be called
a theorem proof.

Product research uses
`benchmarks/research_capability_ladder_20260814.json`. The immutable cross-family
protocol `benchmarks/autonomous_cross_family_e2e_protocol_20260713.json` remains
the S13 integrated formal-capability authority and is not weakened by this split.

## Minimal harness principle

The harness protects execution and evidence; the model owns research content.

```text
model selects an action or writes an artifact
  -> real literature, Python, R, simulation, or Lean tool runs
  -> raw observation returns to the same source-owning model
  -> model revises, reports a grounded gap, or stops
```

Runtime may enforce identities, hashes, task intent, source visibility, isolation,
budgets, frozen gates, and proof promotion. It must not encode statistical answers,
patch source, interpret Lean errors into tactic recipes, or route ordinary local
failures through a repair hierarchy.

This follows the useful common denominator of frontier systems rather than copying
their full orchestration stacks:

- [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) and
  [Numina Lean Agent](https://arxiv.org/abs/2601.14027): small tool loop, complete
  source ownership, and direct environment feedback;
- [ERA](https://github.com/google-research/era): generate, execute, score, and
  search only where an executable objective is reliable;
- [AI Co-Scientist](https://arxiv.org/abs/2502.18864): generate, debate, rank,
  evolve, and meta-review hypotheses where no exact scorer exists;
- [AI Scientist-v2](https://arxiv.org/abs/2504.08066): end-to-end experimentation
  with explicit failure evidence rather than demo-only outputs;
- [Read the Paper, Write the Code](https://arxiv.org/abs/2604.21965): evaluate
  paper understanding by executable reproduction, not textual similarity alone;
- [LeanMarathon](https://arxiv.org/abs/2606.05400): use a durable statement/lemma
  DAG and verifier-backed checkpoints for long-horizon formal work.

## Progressive research graph

The default order is progressive commitment, not a rigid waterfall.

```text
task intent and source-visibility policy
  -> literature/code/data scout
  -> exact public replication when available
  -> theory workspace and claim DAG
  <-> exploratory implementation and falsification
  -> independent theory/source review and stable checkpoint
  -> frozen confirmatory protocol and precision budget
  -> confirmatory execution
  -> optional/advisory/required deep formalization
  -> final evidence vector and gap ledger
```

Search begins early when the task allows external evidence. For a published result
with public code and data, the first scientific act is to rerun the exact pinned
artifact. Reimplementation follows only after the environment and claimed target
are understood. The manifest distinguishes author code, model code, and reused
library code by source snapshot and hash.

TheoryDeveloper is a persistent workspace, not one JSON answer. It maintains
definitions, assumptions, equation lineage, a lemma/claim DAG, counterexamples,
sanity checks, and unresolved gaps. Independent review and empirical or formal
observations can reopen the current theory lineage. A model-reported theory gap is
an honest blocked result, never proof evidence.

The mathematical authority is now model-authored Markdown, LaTeX, and BibTeX in a
content-addressed workspace. The structured handoff carries claim/document anchors,
theorem summaries, and typed cross-agent ABIs, but it is no longer the authority for
the derivation. It is still a transitional payload and should be reduced further as
consumers move to references. Reviewers, coding agents, simulation agents, and hidden
evaluators consume the same hash-verified document bytes; schema validity cannot stand
in for mathematical validity.

A schema-valid theory write does not automatically close the workspace. The author
model explicitly commits a review checkpoint or continues within the existing
bounded session; the harness imposes no fixed review ritual. Independent theory
evaluation remains authoritative, so model self-commitment earns no correctness
credit by itself.

Algorithm and exploratory Simulation may begin as soon as the estimand, DGP,
procedure ABI, and consumed claims are stable enough to execute. They need not wait
for every theorem lemma. Exploratory outcomes may challenge theory but remain
non-confirmatory. Confirmatory code is accepted only against the current reviewed
theory checkpoint and a frozen measurement protocol.

A light formal scout may run in parallel to identify missing definitions, library
APIs, or an ill-posed theorem statement. Expensive proof search normally waits for
statement stability. `proof_first` tasks may reverse that order, and `dual_track`
tasks may run both. Formal gaps block only when the frozen task contract marks the
formal dimension required.

## Simulation precision

There is no general scientific reason to use exactly 100 replications. Before
confirmatory outcomes are visible, the evaluator freezes one of:

- a target Monte Carlo standard error;
- a target confidence-interval width;
- a power or rare-event precision target;
- a fixed resource budget with the resulting uncertainty reported.

The replicate count follows from the selected criterion and task geometry.
Exploratory runs may be cheaper and adaptive, but their labels and seeds cannot be
promoted to confirmatory evidence. Confirmatory stopping may depend on a predeclared
precision statistic, never on whether the scientific result looks favorable.

A failed confirmatory outcome terminates that candidate lineage for the scored run.
It may motivate a separately registered follow-up study, but it is not returned to
the same source model for result-informed rewriting and another nominally
confirmatory execution. Independent source review still runs before outcome release,
then the task continues only to unvisited evidence lanes and the final gap report.

## Evidence vector

Each task freezes `required`, `optional`, or `not_applicable` for these dimensions:

- `source_replication`: exact rerun of supplied public code/data;
- `theory`: definitions, assumptions, derivation/claim lineage, and review;
- `scientific_code`: model-authored Python or R execution and source review;
- `empirical`: frozen confirmatory results and Monte Carlo uncertainty;
- `formal`: exact target identity, Lean feedback, semantic review, and kernel proof;
- `novelty`: comparison against the task's allowed source horizon;
- `unresolved_gaps`: explicit remaining defects and their evidence.

There is no scalar score that can hide a required failure. Reports may summarize
coverage, but they retain the status and evidence references for every dimension.
Evidence from another task, source hash, cohort, replay fixture, or weaker theorem
cannot close the current dimension.

## Benchmark ladder

Evaluation should become harder only after the preceding level is reliable.

| Level | Task | Model-visible material | Gold authority |
|---|---|---|---|
| L0 | Focused known-result unit | statement and minimal setup | curated theorem, code, or numeric invariant |
| L1 | Exact published replication | paper, author code, data | pinned environment and published outputs |
| L2 | Paper-to-code reproduction | paper and data, author code hidden | hidden source and result distributions |
| L3 | Known-theory rederivation | problem and assumptions, result/proof hidden | independent theorem and proof rubric |
| L4 | Historical rediscovery | pre-publication source horizon | later published theory/code/results |
| L5 | Near-frontier extension | base paper, extension target | later or independently curated result |
| L6 | True open problem | permitted contemporary sources | no answer gold; evidence and gap audit only |

L0-L3 measure correctness and mechanism reliability. L4-L5 test research-like
rediscovery under time and source controls. L6 measures research process,
falsifiability, and honesty; it cannot establish scientific correctness merely
because several LLM reviewers agree.

The initial L0-L2 candidates in the ladder file are curation proposals, not live
gold. Each must obtain immutable paper/code/data snapshots, independent expected
artifacts, environment lockfiles, and leakage review before activation. Their
answers must never enter runtime prompts, general RAG, policy packs, or source code.

## Leakage and independence

Every scored run records:

- exact model `claude-haiku-4-5-20251001` for all live evaluation calls;
- task release, source-horizon, paper/code/data visibility, and snapshot hashes;
- fresh-start state and disabled task-learning memory;
- model-authored versus supplied artifacts;
- independent reviewer context and result blinding;
- frozen metric and simulation-precision contracts;
- seeds/cohorts hidden until execution and fresh cohorts after outcome-driven edits;
- all web, repository, and RAG handles actually exposed to the model.

Gold artifacts live outside accessible RAG and model workspaces. Held-out outcomes
cannot motivate task-family validators, prompts, aliases, or fixtures. Shared
harness defects found on development tasks may be repaired only when the change is
content-independent and tested across unrelated families.

## Strict formal-capability protocol

The existing cross-family development panel remains:

- `right_censored_survival_km`
- `sequential_anytime_bernoulli`

Its held-out panel remains sealed:

- `high_dimensional_spiked_pca`
- `extreme_tail_quantile_hill`

Every task in that protocol still requires a fresh Architect plan, model-authored
theory and scientific source, independent review, task-bound formal retrieval,
raw Lean feedback, exact target identity, and local kernel closure. Support lemmas,
RAG hits, pseudo-formalization, or simulation cannot substitute for closure.

## Efficiency contract

Evaluation records calls, latency, token use, tool turns, source hashes, and repeated
finding fingerprints. It fails harness efficiency when it resets a lineage budget,
repeats an unchanged owner/finding/source cycle without new evidence, routes routine
source failures through Architect, executes confirmatory work before its gates, or
copies recursive payloads into manifests.

Deterministic replay is appropriate for harness regression tests. It is never live
model capability, fresh scientific execution, novelty, or proof evidence.

## Current evidence

The latest immutable exact-Haiku v436 development run remains diagnostic: both
tasks ended `BLOCKED`, integrated capability was 5/16, and exact theorem closure
was 0/2. Survival reached real generated-code and simulation execution, but a
model-authored semantic positive control contradicted its own frozen numeric
gate and was correctly rejected. Sequential made two substantive theory
revisions but did not establish that numerical quadrature preserves its claimed
e-process guarantee. Neither task reached Formalizer, so the atomic Lean
declaration-context improvement still has component evidence only. The held-out
strict-formal panel remains sealed.

The ladder now has five full-task-gold L0 tasks. White HC0 has one fresh
corrected-v2 exact-Haiku run. v5 ended `BLOCKED`: its accepted estimator
passed all 7 hidden reference/metamorphic checks and all 6 hidden empirical checks
across two DGPs and 2,000 estimator calls, but its theory passed only 7 of 11 hidden
checks. It omitted required design/variance-limit, triangular-array/moment, and
aggregate-meat arguments and retained an invalid unscaled nonzero covariance limit.
The frozen runtime simulation also failed one of six metric gates, so hidden
empirical support is reported separately and does not turn the runtime protocol or
the full task into a pass.

The second task, Kaplan-Meier/Greenwood, now has one fresh exact-Haiku v2 run. An
earlier v1 attempt failed at the Anthropic tool-schema boundary before TheoryDeveloper
received a model turn and is not a capability draw. In v2, TheoryDeveloper authored
two authoritative Markdown documents totaling 17,928 bytes, the runtime completed
its research loop, and the exact accepted estimator passed all 10 hidden algorithm
checks and all 6 hidden empirical checks across two DGPs and 2,000 calls. Formalization
was correctly not applicable.

The full KM task is nevertheless not validated. The runtime theory preflight accepted
an incoherent censoring-independence statement and a displayed asymptotic-variance
integral with an extra survival factor. The first private theory scorer returned
10/13, but its three failures were notation or wording false negatives: equivalent
LaTeX Greenwood, risk-set, and scaling statements were rejected while the substantive
errors were missed. That scorer therefore failed calibration and its raw count is not
a semantic capability score. TheoryDeveloper also labeled its own pre-review
scratchpad outcomes as confirmatory and selected acceptance thresholds before the
independent frozen simulation lane. The frozen v2 artifact remains a negative
calibration case; it will not be resampled or rewritten to fit the task.

The corrected v2 statement distinguishes `V_HC0 = O(n^-1)` from
`n V_HC0 -> Q^-1 Omega Q^-1` and requires design and moment regularity beyond
finite-sample full rank. The evaluator binds every result to the exact visible
question hash, so the retired v1 runs cannot receive v2 credit. The real evaluator
bundle is operator-provisioned outside the repository and model-visible workspace;
the public tree contains only its content hashes and non-capability unit-test
fixtures. The private authority now checks the exact accepted theory packet,
estimator source, and MCSE-calibrated homoskedastic and heteroskedastic behavior.
It rejects the retired v4 theory scaling, accepts a corrected reference packet,
passes an independently implemented estimator on every hidden dimension, runs in
an ephemeral sandbox, and persists neither evaluator paths nor check identities,
thresholds, observed values, or harness source. The v5 hidden results are model
component evidence, not full-task success. v5 also exposed an efficiency defect:
the pre-fix runtime used the failed confirmatory outcome for one source rewrite and
second execution, then accepted an Architect `BLOCK` packet whose own rationale
said Critic was the required terminal reporter. The shared fix removes that
post-outcome source backedge and requires terminal gap reporting without changing
models, thresholds, retries, or budgets. It has deterministic regression evidence;
there is no post-fix live rerun.

A claim-anchored semantic authority has now been calibrated on the frozen reference,
independent negative variants, and exact KM v2 documents. It runs once under hidden
post-runtime evaluator authority with exact Haiku and no retry or tier escalation.
The model classified only four of five unlabeled calibration cases correctly and
also marked the known-bad candidate `PASS`. The calibration gate therefore failed
closed. The candidate receives no theory credit, while its independently hidden
algorithm and empirical passes remain intact. This is an evaluator diagnosis, not a
fresh research draw.

The completion contract now also requires the exact hash-bound theory preflight and
an explicit per-dimension terminal Critic disposition. A Critic manifest can no
longer bypass preflight, ambiguous legacy simulation flags are excluded from the
Critic view, and task intent determines which dimensions are required, optional, or
not applicable. Full theory documents are transient Critic context; manifests retain
only their canonical-view hash and artifact references. Recomputing frozen KM v2
under this contract gives `research_loop_complete=false` and `full_task_passed=false`.

An exact-Haiku Critic replay with the authoritative Markdown documents nevertheless
still called theory supported and accepted the candidate. Better prompting and full
text alone therefore did not supply reliable mathematical judgment. The next product
step is source-grounded long-horizon theory development and referee reasoning on an
unrelated known result, followed by a pinned published replication. It is not another
KM/HC0 draw, a larger budget, an ensemble vote, or more task-specific guardrails.

The same TheoryDeveloper can now checkpoint substantive Markdown/LaTeX progress and
resume the exact hash-bound workspace under the same owner, including a reviewer-bound
revision. This removes premature acceptance or lost partial mathematics as a harness
constraint, but currently has deterministic replay evidence only. It does not make a
partial checkpoint accepted theory, cross-task research memory, or evidence that the
model can complete a long derivation correctly.

An unrelated James-Stein normal-mean L0 task was frozen before its first runtime
model call. Its model-visible authority is a hash-bound 1961 paper extraction plus a
page-bound transcription of the scan's damaged formulas. Evaluator-only gold combines
the generic Markdown/LaTeX identity harness, a 7/7 exact-Haiku semantic calibration,
closed-form and metamorphic estimator checks, and a predeclared paired-risk simulation
with MCSE reporting. The reference estimator passes all five algorithm checks and all
three empirical DGPs; three deliberately wrong estimator families are rejected. These
remain evaluator calibration facts, not model capability.

The single fresh exact-Haiku run scored `0/1`. TheoryDeveloper used the direct
Markdown workspace, searched and read the source snapshot, and made five model-owned
submissions, but it exhausted those submissions with one estimator-to-claim-index link
still missing. It then reported a structural issue as a mathematical gap instead of
checkpointing the 25,240-byte document for same-owner continuation. No independently
accepted theory packet, generated estimator, simulation, or formal artifact resulted.
Formalization was correctly absent by task intent.

The unaccepted document also exposed a more serious scientific-review problem. It
states the correct final James-Stein risk conclusion, but retains false intermediate
noncentral-chi-square equations, circular abandoned routes, and an asserted cross-term
simplification as if they formed a coherent proof. In an evaluator-only diagnostic,
the frozen semantic judge retained its 7/7 calibration yet marked this document
`PASS`. That false acceptance receives no score and shows that final-claim matching is
not a sufficient theory referee. The next unrelated benchmark should evaluate a
generic claim-linked referee that reads the decisive equation ranges, checks each
dependency and countercheck, and distinguishes endorsed derivation from rejected
exploration. It should not trigger a James-Stein rerun, task-specific formulas, more
budget, or a new repair layer.

The existing independent theory preflight has therefore been tightened without adding
another reviewer or model call. In client-tool mode, its runtime now verifies that exact
document reads cover every non-`REJECTED` claim-index anchor before accepting a review;
the model still chooses ranges, reconstructs mathematics, tests counterexamples, and
owns every verdict. At the same time, twenty-one accumulated prompts about particular
failure patterns were replaced by seven general scientific-review principles. This is
inspection-provenance and harness-simplification evidence only. It does not repair or
rescore James-Stein, make line coverage equivalent to correct judgment, or establish
improved live theory capability until a future unrelated frozen task exercises it.

The Student-t normal-mean L0 benchmark was frozen before its first runtime model call.
It contains one distribution theorem, one interval algorithm, and one MCSE-aware
coverage target. Its model-visible authority is a hash-bound 1908 source snapshot with
an explicitly identified modern-notation transcription; deep formalization, novelty,
and source-code replication are not required. The evaluator bundle remains outside the
repository and all model/RAG workspaces. Before activation, the reference
implementation passed six direct and metamorphic checks and three predeclared normal
coverage DGPs with 3,000 replicates each, while three deliberately wrong estimator
families were rejected. The isolated exact-Haiku semantic authority classified all ten
unlabeled calibration cases correctly and passed its reference candidate. These are
evaluator calibration facts, not research capability.

The one permitted fresh exact-Haiku draw completed the canonical non-formal research
loop. Runtime returned `ACCEPTED`; `research_eval` was 1/1 complete and mode-conformant;
the seven enabled LLM roles all used `claude-haiku-4-5-20251001`. TheoryDeveloper used
the persistent file workspace to write a 5,308-byte Markdown derivation, explicitly
committed its checkpoint, and was accepted by the independent preflight. One generated
algorithm and one generated simulation then executed and passed their runtime semantic
reviews, and the terminal Critic accepted. Formalization was correctly not applicable.

Hidden post-runtime evidence remains split by dimension. The exact accepted estimator
passed 7/7 algorithm checks, the empirical result passed 6/6 checks over 9,000 hidden
estimator calls, and the theory artifact passed 5/5 identity checks. However, the
hidden claim-level theory semantic call failed closed with an unclassified `ValueError`
before any verdict. Therefore theory is not gold-validated and the full task remains
`0/1`; runtime acceptance, coherent-looking Markdown, and component passes cannot fill
that missing authority. The task will not be rerun or rescored to seek a favorable
model or evaluator draw.

The run exposed two shared product-design defects. TheoryDeveloper itself read the
permitted 1908 snapshot, but the independent referee had only compact runtime context
and formal-library retrieval, so its three optional source searches were irrelevant
Lean-library searches. The same hash-bound `search_research_sources` and
`read_research_source` tools are now passed into the existing referee loop. The model
chooses queries and exact ranges; source text is visible only in that active turn and
the packet persists compact snapshot, document, line, and content hashes. This adds no
agent, retry, tool-turn allowance, task-specific source router, or proof claim.

The Architect also expanded one declared empirical target into five required gates and
4,880 runtime estimator calls. The author and independent reviewer prompts now preserve
upstream scientific-claim granularity: undeclared stress settings, nominal levels,
nuisance values, and boundary diagnostics remain exploratory unless upstream makes
them separate confirmatory claims. This is model-owned scientific judgment, not a
hardcoded gate count. Both post-run changes have regression evidence only; 741 tests
pass, and neither change supplies retrospective Student-t capability credit.

Another S13 live run should answer a specific shared-mechanism hypothesis that
already has component or replay evidence; it should not merely resample the same
two broad tasks in hope of a better model draw. This is an evaluation-selection
rule, not a smaller source-workspace budget or an extra runtime guardrail. The
unchanged S13 budgets and exact kernel gate remain authoritative whenever that
formal-capability evaluation is run.
