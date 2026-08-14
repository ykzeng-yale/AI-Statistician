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

The ladder now has one active L0 task, White HC0, with private full-task gold
configured but no passing fresh v2 run. Four exact-Haiku diagnostic runs against the retired
v1 statement each produced independently accepted estimator source that passed
all seven hidden reference and metamorphic checks; none completed the empirical
loop. The fourth theory packet also confused the finite-sample covariance of the
OLS estimator with the asymptotic covariance of its square-root-n limit. Its
independent preflight accepted that normalization error.

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
thresholds, observed values, or harness source. This is evaluator calibration, not
model capability. The next product-evaluation step is one fresh corrected v2 run
under unchanged exact-Haiku budgets before activating another unrelated L0 or L1
task.

Another S13 live run should answer a specific shared-mechanism hypothesis that
already has component or replay evidence; it should not merely resample the same
two broad tasks in hope of a better model draw. This is an evaluation-selection
rule, not a smaller source-workspace budget or an extra runtime guardrail. The
unchanged S13 budgets and exact kernel gate remain authoritative whenever that
formal-capability evaluation is run.
