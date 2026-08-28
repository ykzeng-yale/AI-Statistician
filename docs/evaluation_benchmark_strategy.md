# Evaluation Benchmark Strategy

Updated: 2026-08-21

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

## Visible executable contract

Every newly activated schema-v3 task with a hidden algorithm or empirical
evaluator freezes one model-visible estimator contract before the first model
call. The contract names the `run_estimator` identity and defines every request
and response field by meaning, JSON type, shape, units, indexing, edge cases,
normalization, and stable clause ID. When an empirical evaluator exists, the
same compact contract also names the public empirical claims that evaluator is
allowed to assess. It does not encode general theory claims or derivations:
those remain in the question and model-authored Markdown/LaTeX documents.

Each evaluator-only algorithm or empirical acceptance check must cite one or
more public clause IDs, and every empirical check must cite a public empirical
claim. Its estimator identity must match the public contract. Expected values,
hidden cases, seeds, tolerance values, and harness source remain evaluator-only.
Clause references establish inspectable provenance; they do not mechanically
prove semantic entailment or become runtime guardrails.

Schema v3 adds one executable activation gate before any product-model call. A
hash-frozen reference candidate and one or more hash-frozen negative candidates
run through the exact hidden sandbox, harness, estimator binding, and acceptance
checks later used for model candidates. The reference must pass, every configured
algorithm or empirical evaluator must reject at least one invoked negative, and
the enabled evaluators' checks must collectively cite every applicable public ABI
clause. Historical activation summaries are not certificates for this gate.

This executable calibration catches stale references, vacuous validators, missing
evaluator dimensions, and clause-coverage omissions. It cannot prove a claim over
an infinite input domain or prove that a check's prose citation is truthful. Before
task activation, the operator still audits semantic entailment and uses independent
boundary/property probes appropriate to the declared domain. Those probes live in
evaluator artifacts, not product runtime rules or model prompts.

Theory-semantic activation must also exercise the exact adjudication mode later used
for the product candidate. Concise overall-status calibration cases are necessary but
not sufficient because the live path uses an integrated long document, a claim rubric,
and document-wide contradiction status. Before the first product call, the frozen
authority should pass its complete reference document and reject at least one
realistic long-form near miss through that exact candidate-mode path. The near miss
should preserve plausible headline conclusions while retaining a material active
contradiction, so keyword or final-answer matching cannot pass it. Its source,
judgment, model identity, and hashes remain evaluator-only. This is a benchmark
negative control, not a product formula, prompt answer, repair rule, or post-run retry.

Commit `6d751fb6` makes this executable for new schema-4 authorities. Each
hash-bound near miss is submitted in a separate call under the same integrated
document-status, claim-status, and evidence-reference schema as the eventual
candidate. The frozen full reference is then submitted as the activation candidate.
Private case identities and expected statuses are withheld from every model request;
any false-accepted negative prevents activation before the first product call.
Historical schema-1 through schema-3 draws retain their immutable results.

That audit is performed at the granularity of one hidden behavior, not one
aggregate boolean. Every hidden test vector must be entailed by at least one
explicit visible clause, including missing-field, extra-field, coercion, and
boundary behavior when any of those are scored. An aggregate check may summarize
already declared atomic checks, but it must not introduce another behavior. A
failure whose decisive hidden behavior was never stated in the visible ABI remains
an immutable protocol failure for the consumed draw, but it is not evidence that
the model violated the public contract. This is a benchmark-freeze obligation,
not a product prompt, runtime validator, or source-repair rule.

The full public contract is supplied to the source-owning Theory, Python/R,
Simulation, review, and Critic model contexts. Agent result artifacts do not
recursively copy it; the frozen question and content-derived contract identity
remain authoritative. Schemas v1 and v2 stay read-compatible for immutable
historical evaluation, while canonical live activation requires schema v3. This
adds no agent, route, repair layer, retry, research budget, statistical formula,
or model escalation.

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

Exact source execution schema v2 supports ordinary author scripts that persist
tables, figures, or model files. The operator freezes their relative result paths
before activation; the runner copies only hash-verified snapshot files into an
isolated copy-on-write workspace, executes the unchanged entrypoint, rejects mutated
inputs and undeclared workspace outputs, and returns bounded text or hash/size
descriptors to the same model session. Schema v1 stdout-only manifests remain
read-compatible. Declared outputs are replication observations, not automatically
correct scientific interpretations or hidden-gold acceptance.

Ordinary product tasks may let the same TheoryDeveloper model search Crossref and
public GitHub through opaque-handle tools under an explicit source horizon. Those
live observations support scouting only. L1-L5 evaluation never treats a mutable
API response as gold or exact replication: permitted materials are frozen before
activation, and target-paper blocklists and evaluator-only artifacts remain outside
the discovery provider, RAG, and model workspace.

When live discovery is allowed, the independent theory referee may use a separate
opaque-handle session to seek contrary papers or implementations. The harness never
chooses a query or source. Search metadata is not citable; only content the referee
explicitly reads is hash-bound into review evidence, and it remains non-proof
literature evidence. Frozen and historical benchmarks keep this capability disabled.

TheoryDeveloper is a persistent workspace, not one JSON answer. It maintains
definitions, assumptions, equation lineage, a lemma/claim DAG, counterexamples,
sanity checks, and unresolved gaps. Independent review and empirical or formal
observations can reopen the current theory lineage. A model-reported theory gap is
an honest blocked result, never proof evidence.

Within one TheoryDeveloper segment, reads, searches, writes, edits, and scratch work
draw from one ordinary-action budget. Evaluation must not prescribe class-specific
read or write counts: the model decides how to spend its workspace actions, while the
harness preserves the total turn/action boundary and the separately reserved terminal
checkpoint or gap disposition.

The mathematical authority is now model-authored Markdown, LaTeX, and BibTeX in a
content-addressed workspace. The structured handoff carries stable claim IDs, exact
document paths, statuses, direct dependency edges, and only the typed ABIs selected
by task intent; it does not require a Markdown anchor grammar and is not the authority
for the derivation. Theorem cards and proof plans are Lean-facing handoffs and are not
required for non-formal theory; theorem identity and dependencies already live in the
document-backed claim DAG. The remaining structured payload is transitional and should
shrink as consumers move to references. Reviewers, coding agents, simulation agents,
and hidden evaluators consume the same hash-verified document bytes; schema validity
cannot stand in for mathematical validity.

Independent mathematical review follows the same rule: the referee's substantive
argument is one model-authored Markdown/LaTeX report, while the structured submission
contains only ordered task-derived component statuses, exact report-line spans, evidence
references, and compact blocking findings. Several components may share one span.
Runtime may bind identities, hash and persist the report, and derive routing; it may not
duplicate, summarize, repair, parse, or choose the referee's mathematics.
The referee chooses exact ranges and source reads around the highest-risk load-bearing
claims and begins from attempted falsification; evaluation must not require exhaustive
paraphrase as a proxy for scrutiny. A hidden theory-semantic judge receives the same
canonical candidate authority as runtime consumers: hash-verified Markdown/LaTeX plus
the model-authored executable ABI projection. It must not silently discard either half
or require mathematical prose to be duplicated into JSON.

For future draws, hidden candidate semantics use one integrated document context, not
one isolated model call per rubric claim. The calibrated judge returns both a
document-wide status and keyed per-claim statuses in the same structured response.
The document-wide status can reject any material active falsehood even when every
listed rubric claim is satisfied; deterministic aggregation fails when either the
whole-document judgment or a required claim fails. This reduces candidate calls from
one per claim to one per document set and preserves cross-claim contradictions. It is
post-runtime evaluator authority only and cannot revise or route the candidate.

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

Fresh model-authored Simulation source follows one source-owner lifecycle before
confirmation. The same session authors and executes a separate-seed exploratory
diagnostic, receives the raw sandbox observation, may revise its source, and then
explicitly commits exact bytes. This diagnostic can test imports, interfaces,
invariants, numerical stability, and the model's own scientific expectations; it is
never confirmatory evidence. The exact committed bytes then execute once in the
isolated blinded confirmatory sandbox against the frozen cohort and metric protocol.
The confirmatory outcome is withheld from the source owner.

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

The ladder now has six full-task-gold L0 tasks. White HC0 has one fresh
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

The Gaussian Model-X L2 benchmark was then frozen before its first runtime model
call. The model-visible snapshot contains the 2018 paper but not the author package;
the evaluator-only bundle pins the hidden implementation and separately validates
theory semantics, sampler behavior, and joint empirical moments. Before activation,
the reference implementation passed 7/7 algorithm checks and three 12,000-row DGPs,
four wrong implementations were rejected by both algorithm and empirical harnesses,
and exact Haiku classified 10/10 sealed semantic calibration cases correctly. These
remain evaluator calibration facts, not system capability.

The one permitted fresh exact-Haiku draw remained `BLOCKED` and scored `0/1`.
TheoryDeveloper searched the paper twice, read four exact source ranges, wrote one
13,130-byte authoritative Markdown document plus compact handoffs, and explicitly
checkpointed unfinished anchor work. The next same-owner task was rejected before a
model call because initial workspace identity included the transient scheduling
`task_id`; a legitimate continuation necessarily receives a new ID. No theory packet
reached independent review, and no algorithm, simulation, hidden evaluator, or
Formalizer ran. Formalization remained correctly absent by task intent.

The frozen document is also a useful unaccepted mathematical hard negative. It
contains an incorrect joint-covariance quadratic-form expansion, treats symmetric
two-by-two block structure as sufficient for arbitrary coordinatewise swaps, and
gives an incomplete conditional-covariance PSD argument. These defects must be found
by model self-check and independent review, not by encoding Gaussian-knockoff algebra
in the runtime. A correct transport mechanism would not make this document accepted
theory.

The shared continuation defect is fixed by excluding only transient `task_id` from
the initial authoring binding while retaining the exact question, prompt mode,
Architect proposal, objective, tool contract, and other frozen context. The existing
TheoryDeveloper prompt now also asks the same model to recompute pivotal identities,
test minimal and boundary cases, and correct or mark unresolved claims before a
checkpoint. No retry, turn, submission, model tier, agent, scheduler, task formula, or
content repair was added; 746 tests pass. The task is not rerun or rescored, and both
changes have regression evidence only.

The same frozen trace also showed that outer RetrievalMemory queried and persisted
Lean declaration context even though the task declared formalization not applicable.
RetrievalMemory now preserves paper and general knowledge scouting but makes no Lean
provider call, tool record, or topology payload for that explicit task intent. Formal
`optional`, `required`, and legacy tasks retain their prior retrieval behavior. This
is a task-intent conformance simplification with regression evidence only; it does not
change the frozen run or remove the Formalizer and Statlib RAG capabilities.

The unrelated survey-sampling L0 task was frozen before its first runtime model call.
It asks for one finite-population Horvitz-Thompson total theorem, one sampled-sum
estimator ABI, and one joint design-moment assessment under independent Poisson
sampling. Before activation, the reference implementation passed 8/8 direct and
metamorphic checks and all three 12,000-replicate design-moment DGPs, four executable
but statistically wrong variants were rejected by both hidden lanes, and exact Haiku
classified 10/10 isolated semantic calibration cases correctly. Those remain evaluator
calibration facts, not model capability.

Exactly one exact-Haiku draw then ran under the frozen authority. TheoryDeveloper wrote
one 9,001-byte authoritative Markdown derivation and a document-backed claim index,
but the non-formal contract also required duplicate theorem cards and a proof plan.
All five writes were consumed aligning those redundant IDs, after which the model
reported a structural mismatch as a theory gap. Runtime ended `BLOCKED`, research and
hidden gold remained 0/1, independent theory review did not run, and no generated code,
simulation, or Formalizer execution occurred. The task is frozen and will not be
rerun or rescored.

The shared correction removes theorem cards and proof plans from required non-formal
handoffs while preserving them for selected formal authoring and exact kernel gates.
The same run also confirmed zero Lean retrieval calls, but its top-level manifest still
copied an irrelevant 57,753-declaration provider inventory. Default Lean providers now
initialize only when at least one selected task may use a formal lane; an all-nonformal
run records only a compact inactive descriptor. Neither change adds an agent, retry,
budget, task formula, content repair, or model-tier escalation. All 750 tests pass;
these fixes have regression evidence only and confer no credit on the frozen draw.

The disjoint normal-sample-variance L0 task was frozen before its first runtime model
call. Its evaluator-only reference passed 8/8 direct and metamorphic checks and three
12,000-replicate normal DGPs; four executable but statistically wrong variants were
rejected, and exact Haiku classified 10/10 isolated semantic calibration cases
correctly. Exactly one frozen exact-Haiku draw then reached runtime `ACCEPTED`, one
generated algorithm execution, one generated simulation execution, research evaluation
1/1, and hidden gold 1/1 without entering Formalizer.

That apparent pass is invalid. Operator audit found that the active proof falsely
claimed a difference of independent chi-square variables has the subtracted degrees of
freedom; in the candidate decomposition, the total and removed mean component are not
independent. The same theory document promoted pre-review scratch outcomes to `Frozen
Confirmatory Simulation Results`, and the downstream simulation silently used 2,000
replicates instead of its runtime argument. Both runtime preflight and hidden exact-Haiku
semantic review missed the fatal proof step. The frozen draw therefore remains 0/1 and
will not be rerun, repaired, or rescored. The immutable diagnosis is recorded in
`docs/operator_audits/normal_sample_variance_l0_v1.md`.

The shared post-run correction binds an independent audit row to every active claim,
adds exploratory-versus-confirmatory chronology to preflight, excludes formal-library
context and unverified counts for explicit `formal=not_applicable` tasks, and makes the
existing generated-code reviewer trace declared runtime arguments into source. This
does not add a repair agent, task formula, retry, or model escalation; the source-owning
model still revises its own Markdown/LaTeX or executable source from observations.

Another S13 live run should answer a specific shared-mechanism hypothesis that
already has component or replay evidence; it should not merely resample the same
two broad tasks in hope of a better model draw. This is an evaluation-selection
rule, not a smaller source-workspace budget or an extra runtime guardrail. The
unchanged S13 budgets and exact kernel gate remain authoritative whenever that
formal-capability evaluation is run.

The first disjoint proof-only L0 task now supplies a direct Formalizer component
measurement. Its exact Statlib theorem statement, active Lean project, model policy,
and hidden proof authority were frozen and pushed before one exact-Haiku draw. The
same model-owned Lean workspace made 24 source updates, ran 24 local checks, and made
10 task-bound RAG calls. Its only elaborated declaration depended on `sorryAx`, the
independent axiom audit rejected it, and no candidate reached semantic review or
kernel promotion. Runtime and the one post-termination hidden evaluation therefore
failed, leaving the task at immutable `0/1` and the full ladder at `0/24`.

This is useful failure localization: orchestration reached the correct optional-by-
default but required-by-task Formalizer lane, direct compiler feedback worked, and
the evidence boundary held. It does not establish autonomous Lean proving. Post-run
changes to formal-intent propagation, axiom-audit-aware proof-state observations,
and model-selected active-project declaration inspection are future-task mechanism
evidence only; this task will not be rerun, resumed, repaired, or rescored.

The twenty-seventh consumed task, Uniform endpoint L0 v1, is the clearest current
test of the nonformal research graph. One exact-Haiku draw completed serious
Markdown/LaTeX Theory, isolated artifact review with scratch execution, generated
estimator execution, independent source review, frozen metric review, generated
Simulation execution, independent Simulation review, and terminal Critic. Visible
research evaluation was 1/1 complete and mode-conformant; Formalizer was correctly
not applicable. Hidden gold remained 0/1: mechanical theory passed 7/7 but calibrated
semantic theory failed, the estimator passed six of eight source checks but accepted
an invalid request through permissive NumPy coercion, and empirical evaluation passed
8/8 over 15,000 calls.

This result changes benchmark diagnosis, not the score. The outer graph is now strong
enough to expose scientific-judgment failures instead of routinely stopping on
routing or packet transport. Future disjoint L0 selections should therefore keep one
principal theorem, one explicit executable ABI, and one confirmatory target, while
gold reports retain privacy-preserving per-claim and per-check references. The next
draw must measure whether the same model-owned Theory/referee and source/reviewer
sessions catch decisive mathematics and complete public-interface behavior; it must
not add task formulas, deterministic scientific validators, hidden feedback, retries,
or another scheduler. The immutable ladder remains 0/27.

## Complete-randomization L0 v1 and the Codex harness boundary

The thirty-third scored task was frozen and pushed before its first product
call. It asks for one finite-population complete-randomization result, one
strict Python estimator ABI, and exact assignment enumeration; formalization is
not applicable. The reference estimator passed `15/15`, four wrong estimators
were rejected, exact empirical calibration passed `8/8` over 70 assignments,
and the hidden exact-Haiku semantic authority passed `12/12` calibration cases.
Those are evaluator facts, not product capability.

Exactly one fresh exact-Haiku draw then terminated `BLOCKED` and scored `0/1`.
TheoryDeveloper and its isolated referee completed persistent Markdown and
scratch workspaces; AlgorithmEngineer observed a real execution error and a
provider-truncated unexecuted tool input in the same session, revised its own
source, executed, and committed. The generated-code reviewer similarly recovered
from one invalid terminal envelope in the same isolated session. These events
validate the selectively adopted Codex lifecycle: tool errors are observations,
pending state survives, and no whole subsystem is replayed.

The run failed at the remaining full-packet metric interface. An independent
reviewer found two threshold/measurement contradictions. The same author received
the exact findings but regenerated the complete structured packet, changed its
rationales, and retained both rejected numeric fields. Confirmatory simulation
correctly never ran. Hidden evaluation also found that the accepted source passed
exact empirical behavior `8/8` but only `13/15` strict ABI checks because it
accepted extra request keys and coerced forbidden outcome values.

Operator inspection invalidates the apparent automated theory pass. The final
Neyman formulas are correct, but the Markdown derivation uses the wrong
finite-population correction under its declared normalization, makes false
algebraic equalities, and abandons another derivation before citing a standard
result. The runtime referee and calibrated hidden judge both false-accepted those
steps. Their prompts already require decisive-equation reconstruction, so another
checklist or task-specific formula detector is not the answer.

The post-consumption shared correction gives future metric authoring the same
model-owned source lifecycle as Python/R and Lean. A persistent
`metric_protocol.json` has only exact read and complete-source submission tools;
each submission is parent-hash bound, validator observations return to the same
author transcript, and independent pre-outcome findings return to that same owner.
Commit `e7d0174a` adds no task formula, field patcher, RepairAgent, Architect route,
or scheduler, and its regression evidence cannot change this task's score.

Post-consumption commit `b9ece439` experimented with requiring the same isolated
referee to write an independent reconstruction before candidate-document access and
then revise that report after inspection. A later harness audit found that this
blind-write/read/rewrite chronology prescribed model reasoning order, consumed extra
tool calls, and had no live evidence of improving mathematical judgment. Commit
`6f588ff1` retires that chronology. The referee still owns one hash-bound Markdown
report, exact candidate reads, source and scratch tools, explicit comparison, and a
fail-closed compact verdict, but it chooses the useful action order itself.

Future theory benchmarks should calibrate the simplified mechanism against plausible
incorrect intermediate equations on a disjoint task frozen before its first call.
The complete-randomization draw remains immutable and cannot be rerun, repaired, or
rescored; neither chronology change supplies scientific capability evidence.

## Mann-Whitney U R L0 v1 and external metric state

The thirty-fifth scored task used the same frozen known-result protocol with R as
the required implementation language and formalization marked not applicable. Its
sole exact-Haiku product draw remains immutable `0/1`: the runtime blocked before
Simulation because metric authoring never committed a valid protocol. This leaves
the aggregate at `2/35`; no post-run mechanism may rerun, repair, or rescore it.

The failure sharply separated scientific components from harness liveness. Frozen
authority passed the model-authored Markdown/LaTeX theory `7/7` mechanically and
`7/7` semantically after `9/9` calibration. The exact R estimator passed `14/14`,
and exact empirical enumeration passed `6/6` over all 41 assignments. The isolated
code reviewer voluntarily executed two R falsification probes against exact
hash-bound source and recovered from an invalid terminal envelope in the same
session. Those are component facts, not full-task promotion.

The metric transcript exposed that commit `e7d0174a` was only an intermediate
source-workspace design. Four complete terminal payloads were truncated and never
executed; a fifth 8,041-byte payload reached validation with incorrect top-level
schema. Although the file was persisted, the only write operation still carried
the entire document inside the terminal call, so artifact bytes competed with the
final-disposition budget.

Post-consumption commit `be8d57ab` corrects that shared transport for future tasks.
The model reads a small structural scaffold, applies exact unique-literal edits to
the external file, receives raw validation errors in the same session, and commits
only the current SHA-256. A provider-truncated edit is not executed, and the file
survives for continuation. Runtime owns schema, hashes, and validation; the model
owns every metric and edit. There is no field patcher, scientific rule, retry,
RepairAgent, Architect route, or second scheduler.

A deterministic replay of the consumed prompt projection reduced 54,053 characters
to 25,751 while preserving all 16 authority leaves, the portfolio schema, hard
requirements, and implementation ABI. The full repository passed `887/887` after
the change. This is future-task regression evidence only; Mann-Whitney v1 remains
`0/1` and must never be rerun or rescored.

## Bootstrap L0 v1 and executable source review

The thirty-fourth scored task reconstructed the bootstrap mean and variance theory,
but its accepted estimator violated an explicit no-coercion ABI clause and its
isolated reviewer claimed the opposite. The generated Simulation also failed one of
eight frozen contracts while its reviewer inspected the upstream estimator instead
of the current simulation source. The immutable task remains `0/1`; neither hidden
finding may be fed back to that consumed run.

Future Algorithm review now follows the same minimal agent loop as source authoring.
An isolated reviewer may author and execute a Python or R falsification harness
against the exact hash-bound current estimator, observe the sandbox result in the
same context, and then submit its Markdown judgment. Probe choice, cases, and
interpretation remain model-owned. Runtime owns only source identity, sandboxing,
turn budget, result lineage, blinding, and the final evidence boundary. It does not
translate a diagnostic value into a verdict or source patch.

This mechanism must be evaluated on a new pre-frozen disjoint task. A reviewer may
still choose not to probe or may misinterpret an observation, and regression tests
cannot establish improved scientific judgment. Generated Simulation review remains
source-inspection based until a second cross-task failure justifies a similarly
general executable interface; one bootstrap-specific failure is not enough reason
to invent a Simulation probe ABI.

## Kendall tau-a L0 v1 and capability attribution

The forty-third fully gold-covered task received exactly one frozen exact-Haiku
draw and one automatic hidden evaluation. Its immutable score is `0/1`, leaving
the aggregate at `4/43`. Formalization was not applicable. Hidden algorithm
authority passed `9/10`, empirical authority passed `9/9` over 24,000 estimator
invocations, and runtime remained incomplete at the terminal Critic.

Automated theory fields require an operator override. The Markdown derivation
uses `1/3` instead of `1/9` for a shared-index kernel-product expectation and
counts only one-third of the overlapping pair-pairs. Those errors cancel to the
standard final variance. TheoryDeveloper scratch, referee scratch, and the
referee's initial report all exposed the contradiction, but the referee later
misread `0.111111...` as `1/3`; the calibrated hidden judge also returned `9/9`.
The task therefore receives no theory capability credit despite those frozen
automated fields.

The trace separately found a shared lifecycle defect. Full 5,000-replicate
execution happened on every source-authoring submission, and a last executed
prototype could remain source-valid after the model failed to commit the
workspace. Future source owners now receive a small separate-seed diagnostic for
execution and output-shape iteration, explicitly commit exact bytes, and trigger
one complete blinded confirmatory execution. A terminal workspace failure blocks
promotion. This changes future harness behavior only; it cannot repair or rescore
Kendall.

This is the intended evaluation discipline: distinguish model-owned mathematical
failure, public-interface code failure, malformed model-authored metric gates,
hidden empirical component success, and a deterministic lifecycle fail-open. Do
not collapse them into a single repair target, add a Kendall formula parser, or
use hidden results as feedback. Production serious theory remains a Sonnet role;
all benchmark calls remain exact Haiku under the frozen model policy.

## SRSWOR finite-population mean L0 v1

The forty-seventh fully configured task received exactly one frozen exact-Haiku
product draw and one post-runtime hidden evaluation. Runtime completed the
canonical non-formal research loop and returned `ACCEPTED`; hidden full-task
authority returned `0/1`, so trustworthy aggregate capability remains `4/47`.
Formalization was explicitly not applicable.

Component evidence is intentionally not collapsed into that outcome. Hidden
theory authority passed `7/7` mechanical checks and a calibrated ten-claim
semantic review. Hidden empirical authority passed `6/6` over 96,000 exact
estimator invocations. Hidden algorithm authority passed `11/12` and rejected the
task because the accepted Python estimator silently coerced a numeric string even
though the public contract forbids coercion. The source-owning smoke test tried a
nonnumeric string only, and the independent code reviewer false-accepted after
both of its self-authored probes failed without invoking the estimator.

Operator review separately invalidated the task. The main finite-population
theorems are correct, but the authoritative Markdown contains a false displayed
binomial expansion, loses singleton undefinedness in its constant-population
section, and gives an insufficient large-`N` condition for the with-replacement
comparison. The metric protocol also contains wrong arithmetic for both fixed
populations and uses a constant population for a vacuous mean-unbiasedness check.
Generated Simulation happened to recompute reference quantities from arrays, so
its executable metrics passed despite the wrong protocol prose.

Commit `3b28df58d3ac03af48d7f855ba912725d3324aa3` is a future-task harness change,
not a repair. A code reviewer that elects to execute a probe can no longer submit
`ACCEPT` unless at least one probe executes successfully and invokes the exact
hash-bound estimator. Probe failures and terminal-validation feedback return to
the same reviewer session for model-owned correction. No SRSWOR rule, contract
case, source patch, repair agent, retry scheduler, or model escalation was added.

Commit `1fef5179113566b0b0a64818930771d546c22987` applies the same general loop to
future pre-execution metric review. The isolated reviewer may choose the shared
Python/R/SymPy scratch tool, receives raw output in the same session, and then owns
its terminal scientific judgment. Runtime validates only the frozen input identity,
tool lifecycle, lineage, and compact envelope. It does not supply or interpret a
finite-population formula, derive a threshold, or patch the protocol. Detached
one-shot generated-code review and JSON-only TheoryDeveloper core generation were
retired; authoritative mathematics must remain in the model-owned Markdown/LaTeX
workspace. Regression evidence is `915/915`, not capability credit, and the SRSWOR
draw remains unchanged.

This draw adds a useful benchmark-design rule: hidden empirical scenarios should
include nondegenerate cases capable of distinguishing plausible wrong
implementations, while model-authored public metrics remain an audited research
artifact rather than hidden authority. The task remains immutable and must never
be rerun, repaired, reevaluated, rescored, or resampled.

## BOCD Gamma-Poisson L2 v1

The seventy-sixth fully configured task received exactly one frozen exact-Haiku
product draw and one post-runtime hidden evaluation. Runtime and hidden authority
both returned `0/1`; aggregate trusted full-task capability remains `4/76`.
Formalization was explicitly not applicable and did not run.

The draw validates several architectural choices without establishing correctness.
TheoryDeveloper produced two persistent Markdown/LaTeX documents, scientific code
and Simulation used direct model-tool-observation loops, exact estimator bytes ran
in the sandbox, independent reviews were hash-bound, and the terminal Critic kept
missing empirical evidence inconclusive. No JSON mathematics, RepairAgent, second
scheduler, provider fallback, Sonnet, Opus, or compulsory Lean lane was involved.

Operator review overrides the frozen automated theory fields. One part of the
theory correctly derives `Gamma(a+x,b+1)` while a later active section reverses
the sufficient statistics to `shape=a+r, rate=b+sum(x)`. The independent referee
quotes both forms and still returns `ACCEPT`; the calibrated hidden semantic judge
returns eight of eight claims satisfied. A passed long-form activation near miss
therefore does not make a single Haiku semantic call a correctness oracle for every
long-range contradiction. Frozen scores remain immutable, but trusted component
credit must still yield to direct operator counterevidence.

The generated estimator implements the same reversed state update. Hidden exact
execution shows that causality, normalization, row-zero identity, determinism, and
long-sequence stability can all pass while core numerical semantics are wrong. A
reviewer probe that checks only those self-consistency properties is not a
discriminating oracle. Future reviewers are asked, in the existing prompt and same
session, to compare load-bearing transitions side by side and attempt one
independently derived discriminating check before claiming numerical correctness;
runtime still chooses no formula, case, verdict, or edit.

The final Simulation review correctly requested source revision, but its producer
task retained both stale scientific-progress state and a new semantic-revision
state. Runtime rejected the overlap before another model call. Commit `b9297aef`
makes semantic revision the sole continuation mode while preserving exact reviewed
source, upstream artifacts, and raw findings. This is a shared lifecycle correction,
not a retry or a repair of BOCD. The consumed draw is unchanged and hidden/operator
findings never enter its source-owner context.

The shared panel passed `161/161` and the complete repository passed `1001/1001`
in 81.48 seconds at 149,993 production Python lines. These are regression facts for
future tasks, not retrospective Task 76 capability evidence.

## De-biased Lasso known-precision L2 v1

The seventy-seventh fully configured task received exactly one frozen exact-Haiku
product draw and one post-runtime hidden evaluation. Runtime and hidden full-task
authority both returned `0/1`; aggregate trusted capability remains `4/77`.
Formalization was explicitly not applicable and did not run.

The draw again separates a working model/tool loop from scientific correctness.
TheoryDeveloper produced a persistent 225-line Markdown/LaTeX derivation, but active
sections give opposite KKT signs, the remainder bound uses an infinity norm where the
L1 Lasso error is required, and the stated log-rate does not imply its own sparsity
conclusion. The independent referee repeats the sign error and false-accepts. Hidden
theory mechanics passed 7/7, while the calibrated semantic result was already
`INCONCLUSIVE` at seven of eight claims. Operator findings further invalidate the
positive KKT and remainder assessments.

The accepted Python estimator computes the central de-biasing quantity accurately:
hidden numerical and determinism checks passed, and hidden empirical authority passed
5/5 over 3,000 exact calls. It still violates the visible closed ABI by coercing
values, accepting forbidden JSON types, omitting exact key-set enforcement, and not
enforcing declared dimensions. Hidden algorithm authority correctly failed its
aggregate public-contract check. Numerical success and empirical component evidence
therefore do not become scientific-code capability credit.

The run exposed two future-only shared harness defects. First, TheoryDeveloper
re-authored a lossy interface summary even though the visible question carried a rich
frozen execution contract. Frozen authority must travel by exact immutable reference
and hash; model-authored explanatory notes may supplement but never replace it.
Second, a 128-replicate authoring diagnostic treated
`acceptance_passed=false` as a tool error. After independent review required at least
1,000 replicates, the same Simulation owner could not both honor that protocol and
make the diagnostic scientifically pass. Tool execution validity and scientific
acceptance must be separate observations.

These are Codex-style harness invariants, not content repairs: stable tools, exact
inputs, raw observations, one persistent source owner, and clean termination. No
de-biased-Lasso formula, hidden case, deterministic equation parser, new agent,
retry, fallback, scheduler, or model escalation should enter product runtime.
Task 77 remains immutable and must never be rerun, resumed, repaired,
hidden-evaluated again, reevaluated, rescored, resampled, or supplied its
hidden/operator findings as source-owner feedback.
