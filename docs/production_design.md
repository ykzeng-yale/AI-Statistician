# AI Statistician Production Design

This folder is the production-oriented successor to `Preliminary Attempt/`.
The goal is not to make a bigger interview demo. The goal is a system whose
claims are auditable:

1. The theory layer emits only estimator families with registered formal
   obligations.
2. The formal layer proves Mathlib-backed obligations through a verifier.
3. The algorithm layer uses vetted implementations for the estimator family.
4. The simulator measures bias, RMSE, empirical SE, estimated SE, and 95%
   coverage.
5. Retrieval is audited over the full local statistics proof bank rather than
   treated as a hard-coded lemma lookup.
6. Every run writes a JSON trace that can be used for debugging, evaluation,
   and future training.

## Current Architecture

```text
StatisticalQuestion
  -> TheoryDeveloperAgent
       EstimatorSpec + formal obligation IDs
  -> FormalVerifierAgent
       ProofBank/OpenProver-token retrieval -> AXLE verify_proof
  -> AlgorithmEngineerAgent
       registered implementation + code hash
  -> SimulatorAgent
       DGP, Monte Carlo metrics, feedback
  -> SystemReport
       ACCEPTED | FORMAL_BLOCKED | SIMULATION_BLOCKED
```

`StatisticalQuestion` can come from the built-in registry or from JSON. External
questions may name a supported `dgp_family` and `estimator_family` explicitly,
or the intake layer can infer them for the supported families below. Unsupported
or ambiguous questions fail before simulation rather than silently inventing
unsupported formal guarantees.

## Next-Stage Research Lab

The broader target is not only a registered estimator executor. It is an AI
statistical theory lab that can accept paper-style open questions and produce an
auditable research trace:

```text
OpenResearchQuestion
  -> ProblemFormalizer
       problem class, DGP sketch, estimand, assumptions, asymptotic regime
  -> TheoryPlanner
       candidate estimator/test/procedure, informal derivation, theorem goals
  -> KnowledgeRetriever
       method cards + local Lean/proof-search resources + AI-for-math papers
  -> FormalSubclaimProver
       AXLE/mock verification for Mathlib-backed subclaims
       explicit FORMAL_GAP records for frontier theorem pieces
       Lean-facing theorem skeletons exported for each gap
  -> ResearchSimulator
       problem-specific Monte Carlo environment and diagnostics
  -> ResearchReport
       theory plan + proof status + simulation evidence + limitations
```

The CLI entry point is:

```bash
python3 -m ai_statistician.cli research-benchmark \
  --question-file examples/research_questions.json \
  --runs 100 \
  --out runs/research_benchmark
```

The same loader accepts paper-style Markdown/text files. A Markdown file may use
sections of the form `## question_id: Title`, an optional `Tags:` line, and a
free-form abstract-style description:

```bash
python3 -m ai_statistician.cli research-benchmark \
  --question-file examples/research_paper_abstracts.md \
  --runs 100 \
  --out runs/research_paper_benchmark
```

Real AXLE verification for the Mathlib-backed subclaims:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli research-benchmark \
  --real-lean \
  --runs 60 \
  --out runs/research_benchmark_axle
```

Research trace audit:

```bash
python3 -m ai_statistician.cli research-trace-audit \
  --run-dir runs/research_benchmark \
  --out runs/research_trace_audit
```

The audit validates that each research trace matches the benchmark manifest,
contains the extracted problem specification, source-text extraction evidence
for the problem class / DGP / estimand / assumptions / asymptotic regime,
candidate procedures, theorem goals, retrieved knowledge cards, related local
paper/source hits, formal proof/gap records, exported gap skeleton files,
simulation metrics, diagnostic-to-metric coverage, stress-test ledgers, vetted
research algorithm fingerprints, and honest limitations when gaps remain.

The `paper_sources` section is a separate local retrieval layer over the
frontier statistical-theory benchmark and the AI-for-math paper log. For
frontier benchmark papers, `expected_theoretical_results` and
`evaluation_prompt` are recorded as withheld fields and are not used in the
search text, so this grounding layer can be audited without leaking benchmark
answers into the theory planner.

Each simulation row also includes the problem's declared `stress_tests` plus a
compact `stress_test_metrics` object. These rows are intentionally diagnostic
rather than over-claimed: they certify that the simulation layer evaluated the
declared stress scenarios against available metrics, while full theorem-level
coverage for those scenarios remains part of the formal-gap backlog when it is
not already in the proof bank.

Formal gap backlog audit:

```bash
python3 -m ai_statistician.cli research-gap-audit \
  --run-dir runs/research_benchmark \
  --out runs/research_gap_backlog
```

This aggregates every `FORMAL_GAP` across a benchmark run into
`research_gap_backlog_manifest.json` and a Markdown report. Each row links the
unproved theorem goal to its Lean skeleton artifact, proof strategy, required
formal primitives, candidate procedure, retrieved knowledge cards, already
verified subclaims, and retrieved local Lean/StatInference declarations from the
formal-source index. This makes the formalization frontier auditable as a
library-construction backlog rather than leaving it spread across individual
traces. The release-style `research-system-audit` includes this as a gate.

Research source inventory:

```bash
python3 -m ai_statistician.cli research-knowledge-audit \
  --out runs/research_knowledge_audit
```

The knowledge audit now includes a lightweight local-source inventory. It checks
that the lab can actually see the AI-for-math paper collection, Mathlib
Probability and MeasureTheory trees, local StatInference workspaces,
lean-stat-learning-theory, the vendored EmpericalProcessLEAN main snapshot in
`legacy_sources/emperical_process_lean/`, the vendored legacy AI-Statistician
source pool in `legacy_sources/ai_statistician/`, and OpenProver. The vendored
Lean/stat files are treated as source pools, not as the active runtime:
EmpericalProcessLEAN contributes current shared probability/asymptotics/
empirical-process foundations, while legacy AI-Statistician contributes
theorem-hole benchmark JSONL, schemas, and proof-training artifacts. The
inventory records
file counts, extension counts, keyword evidence, and a fingerprint that is also
included in research-trace provenance. This is still a small deterministic
resource index, not a full semantic RAG system, but it prevents the workflow
from claiming to use local formalization resources that are absent.
Trace audit applies the same grounding contract per run: each normalized
problem class must include its primary statistical-method card, at least one
local Lean/stat formal source, and at least one retrieval/search-system source.

Research multi-seed evaluation:

```bash
python3 -m ai_statistician.cli research-eval \
  --question-file examples/research_questions.json \
  --n-seeds 3 \
  --runs 80 \
  --out runs/research_eval
```

This reruns the full open-question benchmark across multiple simulation seeds,
audits every seed-level research trace, and writes
`research_evaluation_manifest.json` with per-question ready rates and
per-procedure metric means/standard deviations. With `--real-lean`, the
Mathlib-backed subclaims are verified through AXLE on every seed run, while
frontier theorem goals remain explicit gaps.

Research capability audit:

```bash
python3 -m ai_statistician.cli research-capability-audit \
  --out runs/research_capability_audit
```

This is the requirement-level audit for the broad AI Statistical Theory Lab
goal. It writes `research_capability_audit_manifest.json` and
`research_capability_audit.md` with rows for intake, problem formalization,
informal theory planning, knowledge retrieval, AXLE-backed proof-bank
subclaims, Lean gap skeletons, vetted algorithms, simulations, traces, frontier
coverage, and the not-yet-achieved arbitrary-frontier-theory target. The current
scaffold should pass `all_current_release_requirements_met=true`; the broader
research goal intentionally remains `goal_complete=false`.

Research system audit:

```bash
python3 -m ai_statistician.cli research-system-audit \
  --runs 100 \
  --out runs/research_system_audit
```

The system audit is the preferred single command for evaluating this layer. It
runs proof-bank retrieval, frontier precision audit, research capability audit,
research knowledge-source audit, research algorithm audit, proof verification,
the frontier research benchmark, and the research trace audit, then writes
`research_system_audit_manifest.json` with gates and artifact paths. With
`--real-lean`, the proof gate and benchmark subclaims use AXLE
`verify_proof`; frontier theorem goals still remain explicit formal gaps unless
they have been added to the proof bank as real obligations.

Research algorithm audit:

```bash
python3 -m ai_statistician.cli research-algorithm-audit \
  --out runs/research_algorithm_audit
```

Research procedures such as `oracle_aipw`, `split_conformal_poly`,
`kaplan_meier_fixed_time`, `median_of_means_mean`,
`neyman_conservative_variance`, `ols_hc1`, `benjamini_hochberg`,
`bernoulli_lr_eprocess`, `spiked_pca`, and `hill_tail_quantile` are
fingerprinted from the Python source that implements the
simulation/evaluation algorithm. Each research trace records the vetted
algorithm ID, version, registry status, and SHA-256 source hash so simulation
diagnostics are tied to implementation provenance.

Research knowledge audit:

```bash
python3 -m ai_statistician.cli research-knowledge-audit \
  --out runs/research_knowledge_audit
```

This validates the problem-aware knowledge layer used in research traces. It
checks that each card points at an existing local source or valid URL, that each
supported problem retrieves its primary statistical method card as the top hit,
and that the trace includes both a local formal source such as Mathlib,
StatInference, EmpiricalProcessLEAN, or lean-stat-learning-theory and a
retrieval/search source such as Lean Finder, Loogle, ReProver, or OpenProver.

Research intake audit:

```bash
python3 -m ai_statistician.cli research-intake-audit \
  --out runs/research_intake_audit
```

The intake audit checks both sides of the paper-style question boundary:
supported examples in `examples/research_questions.json` and
`examples/research_paper_abstracts.md` must normalize into registered research
problem classes, while frontier topics outside the current lab surface in
`examples/research_unsupported_paper_abstracts.md` must route to
`unsupported_frontier_question` instead of receiving invented procedures or
fake formal guarantees. This is also included as a gate in
`research-system-audit`.

Frontier coverage audit:

```bash
python3 -m ai_statistician.cli frontier-coverage-audit \
  --out runs/frontier_coverage_audit
```

This parses `docs/frontier_stat_theory_benchmark.md`, which contains
DOI-backed recent paper-style questions from JASA, Annals of Statistics, JRSSB,
and Biometrika, then runs the deterministic `ProblemFormalizer` on every entry.
The output reports current supported/unsupported coverage by topic and problem
class. The gate only requires that the benchmark parses cleanly; unsupported
rows are expected and represent the research roadmap, not failures.

Frontier precision audit:

```bash
python3 -m ai_statistician.cli frontier-precision-audit \
  --out runs/frontier_precision_audit
```

This validates that every supported frontier classification has direct evidence
in the paper body fields: title, open question, assumptions, or expected
results. It deliberately ignores broad topic labels, so a row under a mixed
topic such as `multiple_testing_conformal_selection` cannot pass merely because
the topic contains useful words. `research-system-audit` includes this as a gate
to keep reported frontier coverage conservative.

Frontier backlog audit:

```bash
python3 -m ai_statistician.cli frontier-backlog-audit \
  --out runs/frontier_backlog_audit
```

This turns unsupported rows in the 60-paper frontier corpus into an explicit
future-theory roadmap instead of leaving them as a raw count. Each unsupported
paper gets a roadmap domain, a missing problem-class name, likely statistical
methods, and required formal primitives. This preserves the honesty boundary:
unsupported topics still do not run through the simulator or proof bank, but
they become auditable library-construction work items.

Frontier smoke benchmark:

```bash
python3 -m ai_statistician.cli frontier-smoke-benchmark \
  --runs 60 \
  --out runs/frontier_smoke_benchmark
```

This selects supported entries from the 60-paper frontier corpus, at most one
per currently supported problem class by default, and runs the full research
workflow on those real paper-style questions. The output includes the selected
paper IDs, the generated benchmark traces, trace audit, and formal-gap backlog.
With `--real-lean`, the Mathlib-backed subclaims are verified through AXLE.
This is a smoke test of executable paper-style coverage, distinct from the
coverage audit's broader classification count.

The current benchmark covers fourteen frontier-style but controlled problems:

- semiparametric ATE estimation with an oracle AIPW estimator;
- split conformal prediction with distribution-free marginal coverage;
- right-censored survival inference with Kaplan-Meier survival estimation;
- robust mean inference with a median-of-means estimator;
- differentially private inference with a Gaussian-mechanism clipped-mean estimator;
- nonparametric regression inference with a polynomial-sieve pointwise estimator;
- Bayesian predictive-distribution-to-prior calibration with a normal-conjugate posterior estimator;
- measurement-bias-adjusted educational assessment ranking with country/item bias correction;
- design-based conservative variance inference for randomized experiments;
- heteroskedastic regression inference with HC1 robust standard errors.
- large-scale multiple testing with Benjamini-Hochberg FDR control.
- sequential anytime-valid Bernoulli testing with a likelihood-ratio e-process.
- high-dimensional PCA signal-subspace inference under a spiked covariance model.
- extreme-value tail-index and high-quantile inference with Hill/Weissman estimators.

This layer is intentionally honest. It does not claim to prove a full JASA/AOAS
paper theorem in Lean. It proves the Mathlib-backed subclaims available in the
local proof bank, for example indicator expectations, probability normalization,
expectation linearity, variance nonnegativity, finite-sample mean unbiasedness,
sieve-relevant finite-sample Chebyshev bounds, and a noised-estimator
Chebyshev bridge. The latter proves that independent
mean-zero additive noise preserves unbiasedness, adds variance, and gives an
error tail bound using `Var(X)+Var(Z)`, which directly supports the private mean
trace's sampling-plus-privacy-noise decomposition. The hard theory pieces such
as AIPW double robustness, asymptotic normality, conformal rank coverage,
sandwich covariance consistency, DP Gaussian-mechanism calibration, privacy
composition, predictive-prior coherence, posterior credible-interval
calibration, IRT measurement-invariance identifiability, rank-functional
uncertainty theory, high-dimensional PCA perturbation bounds, and
regular-variation order-statistic theory are recorded as `FORMAL_GAP` with the missing
formalization work spelled out. Each gap records machine-readable required
primitives such as `conditional_expectation`, `iid_empirical_mean_clt`,
`epsilon_delta_dp_definition`, `davis_kahan_sin_theta`, or `regular_variation`,
and each gap also gets a Lean-facing skeleton under `formal_gaps/*.lean`.
Those skeletons deliberately use placeholder assumptions
named `h_frontier_missing_*`, so they are roadmap artifacts, not verified
theorem claims. The simulator then checks whether the proposed procedure behaves
as expected in the DGP environment, so each trace separates:

- what is already proved in Lean/AXLE,
- which AXLE-verified proof obligations support each theorem goal,
- what has a Lean theorem skeleton but remains a formal gap,
- what is empirically supported by simulation,
- what remains a research-library backlog item.

The theorem-goal support map is deliberately partial. For instance, it can say
that the AIPW double-robustness goal is supported by the proved AIPW expectation
decomposition, or that the private mean error-decomposition goal is supported by
proved additive-noise unbiasedness, variance, and Chebyshev obligations. It
still leaves the unproved conditional-expectation, empirical-process, privacy,
or asymptotic primitives in `FORMAL_GAP`.

The trace audit enforces this chain: every theorem goal listed by a candidate
procedure must appear in the trace-level theorem-goal registry and must be
covered by either a verified Lean subclaim or an exported formal-gap skeleton.
This prevents procedures from carrying undocumented theorem promises.

## What Is Actually Proved

The system includes estimator-level Lean obligations that AXLE has verified:

- `constant_estimator_unbiased`: expectation of a constant estimator is the
  target constant.
- `constant_estimator_variance_zero`: variance of a constant estimator is zero.
- `mean2_estimator_expectation`: expectation of a two-variable mean estimator is
  the mean of expectations.
- `mean2_estimator_unbiased`: if two integrable component estimators are each
  unbiased for the same target, their two-variable average is unbiased for that
  target.
- `affine_estimator_expectation`: for an integrable estimator `X`, the affine
  shrinkage estimator `a*X+b` has expectation `a*E[X]+b`, supporting posterior
  mean and prior-shrinkage traces.
- `affine_estimator_variance`: for an L2 estimator `X`, the affine shrinkage
  estimator `a*X+b` has variance `a^2 Var(X)`, supporting posterior,
  linear-smoother, and bias-adjusted ranking SE traces.
- `mean2_estimator_variance_indep`: for independent L2 component estimators,
  the variance of their average `(X+Y)/2` is `(Var(X)+Var(Y))/4`.
- `estimator_error_chebyshev`: if an estimator has finite second moment and
  mean `theta`, its absolute-error tail probability is bounded by
  `Var(X) / c^2`.
- `mean2_estimator_chebyshev_indep`: combines unbiasedness, L2 closure,
  independence variance additivity, variance scaling, and Chebyshev to bound
  the absolute-error probability of `(X+Y)/2` by
  `((Var(X)+Var(Y))/4) / c^2`.
  This obligation records dependency edges to the expectation, variance, and
  Chebyshev proof obligations; release audits check that the dependency graph is
  known and verified.
- `finite_sample_mean_unbiased`: for any nonzero finite sample size `n`, if
  each component estimator indexed by `Fin n` is integrable and unbiased for
  `theta`, the arithmetic sample mean estimator is unbiased for `theta`.
- `finite_sample_mean_variance_indep`: for pairwise independent L2 component
  estimators indexed by `Fin n`, the arithmetic sample mean has variance equal
  to the sum of component variances divided by `n^2`; this uses Mathlib's
  `IndepFun.variance_sum` finite-sum variance theorem.
- `finite_sample_mean_chebyshev_indep`: combines finite-sample mean
  unbiasedness, the pairwise-independent variance identity, and Chebyshev's
  inequality to bound the absolute-error probability of the arithmetic mean by
  the proved finite-sample variance divided by `c^2`.
- `event_indicator_expectation`: expectation of an event indicator estimator is
  the event mass.
- `finite_event_indicator_mean_unbiased`: for any nonzero finite sample size
  `n`, if every measurable event indexed by `Fin n` has common probability `p`,
  the arithmetic mean of its event indicators is unbiased for `p`.
- `finite_union_bound`: a Bonferroni-style finite union bound
  `μ (⋃ i∈I, A i) ≤ ∑ i∈I, μ(A i)` proved directly from Mathlib's
  `measure_biUnion_finset_le`, supporting conformal coverage counting,
  BH/FDR error decompositions, and finite-horizon anytime-valid error control.
- `event_probability_mono`: event monotonicity `A ⊆ B -> μ(A) ≤ μ(B)`,
  proved directly from Mathlib's `measure_mono`; this is the reusable
  bad-event-containment step used before applying union or tail bounds.
- `independent_event_inter_probability`: event-independence algebra
  `IndepSet A B μ -> μ(A ∩ B) = μ(A) * μ(B)`, proved directly from
  Mathlib's `IndepSet.measure_inter_eq_mul`; this supports independent
  null-p-value decompositions and sequential likelihood-ratio product
  arguments.
- `first_borel_cantelli_limsup_zero`: the first Borel-Cantelli repeated-event
  control lemma `sum μ(A_n) < ∞ -> μ(limsup A_n)=0`, wrapped around Mathlib's
  `MeasureTheory.measure_limsup_atTop_eq_zero`; this supports convergence,
  rare repeated tail events, and sequential monitoring formal gaps.
- `second_borel_cantelli_limsup_one`: the independent-event recurrence
  counterpart `iIndepSet A μ -> sum μ(A_n)=∞ -> μ(limsup A_n)=1`, wrapped
  around Mathlib's `ProbabilityTheory.measure_limsup_eq_one`; this supports
  extreme-tail recurrence and infinite-exceedance arguments.
- `adapted_hitting_after_is_stopping_time`: a discrete adapted-process hitting
  time is a stopping time, wrapped around Mathlib's
  `Adapted.isStoppingTime_hittingAfter`; this is a verified primitive for
  optional-stopping/e-process theorem skeletons.
- `aipw_score_expectation_decompose`: expectation of an AIPW-style contrast plus
  augmentation score decomposes by linearity.
- `variance_nonneg`: variance is nonnegative.
- `variance_indep_add`: variance adds for independent L2 random variables.

These are deliberately chosen because Mathlib already contains the needed
measure/probability facts. The system does not claim a full CLT, MLE
consistency theorem, or semiparametric efficiency proof yet.

## Existing Code Reuse

The package integrates existing systems where appropriate:

- `Preliminary Attempt/` remains archived as the research prototype and eval
  history.
- `OpenProver` is used opportunistically for Lean-style tokenization in
  retrieval if `/Users/yukang/Documents/OpenProver/src` or `OPENPROVER_SRC`
  exists.
- Loogle integration is exposed as a small optional retriever class. It is not
  required for the default offline run.
- AXLE is the real proof-verification backend for `--real-lean`.
- The local formal-source index performs declaration-level retrieval with
  theorem compression features: binder counts, premise heads, conclusion head,
  left/right equality heads, and major symbols. This is the local-first
  counterpart to Loogle/Lean Finder style premise selection and avoids passing
  thousands of irrelevant lemmas to the LLM.
- `formal-source-audit` persists that declaration corpus as
  `formal_source_index.sqlite` using SQLite FTS, giving a cheap local
  candidate-generation pass before Lean-shape reranking and AXLE proof
  attempts.
- The open-question `research-benchmark` path now accepts the same persisted
  backend and the CLI defaults to it. Formal-gap skeletons are therefore
  grounded through the local SQLite FTS + Lean-shape search path used by the
  source audit, not a separate in-memory-only path.
- CSLib is useful to track as an external Lean library for future algorithm and
  proof-search infrastructure work, but it is not yet a priority runtime corpus
  for statistical probability/asymptotic lemmas.

This is intentionally integration-first. Retrieval and proof search should
reuse Loogle, Lean Finder, LeanDojo/ReProver, OpenProver, and AXLE rather than
being rebuilt inside this repo.

## Running

Offline smoke test:

```bash
python3 -m ai_statistician.cli demo --runs 200 --out runs/smoke
```

External JSON question file:

```bash
python3 -m ai_statistician.cli demo \
  --question-file examples/questions.json \
  --runs 300 \
  --out runs/external
```

Partial JSON question file with inferred families/parameters:

```bash
python3 -m ai_statistician.cli demo \
  --question-file examples/partial_questions.json \
  --runs 300 \
  --out runs/partial
```

LLM-gated theory intake for supported families:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli theory-intake \
  --question-file examples/llm_theory_questions.json \
  --llm-theory
```

The LLM proposal agent is deliberately constrained. It may classify a natural
language question into one of the supported families, but the registry still
gates execution. If Haiku proposes `weibull`, `cox_model`, or any other
unsupported family, the system rejects the question before simulation or Lean
verification.

Question JSON contract:

```json
{
  "id": "external_normal_mean",
  "title": "Estimate a normal mean",
  "dgp": "X_i iid Normal(mu=1.25, sigma=2.0)",
  "target": "mu = E[X]",
  "dgp_family": "normal",
  "estimator_family": "sample_mean",
  "true_params": {"mu": 1.25, "sigma": 2.0},
  "n_obs": 100,
  "tags": ["mean", "normal"]
}
```

Supported `dgp_family` values today: `normal`, `bernoulli`, `constant`.
Supported `estimator_family` values today: `sample_mean`,
`sample_variance`, `sample_proportion`, `constant_estimator`.

For these supported cases, the intake layer can parse parameters such as
`Normal(mu=1.5, sigma=0.75)`, `Bernoulli(p=0.42)`, and `constant c=2.25`.
Normal questions can target either the mean (`sample_mean`) or variance
(`sample_variance`) while sharing the same DGP parser.
For unsupported examples such as Weibull hazards, Cox models, missing-data
targets, or semiparametric efficiency questions, the system should currently
return an unsupported-family error and route the request to roadmap work.

Every `demo` run writes one JSON trace per question plus `manifest.json`.
Run, evaluation, retrieval, proof, algorithm, and system-audit manifests include
stable registry fingerprints where relevant. These hashes cover the question
registry, estimator registry, vetted algorithm registry, and proof bank, so a
saved run can be tied back to the exact source registries that produced it.

Trace audit:

```bash
python3 -m ai_statistician.cli trace-audit \
  --run-dir runs/partial \
  --out runs/trace_audit_partial
```

Each per-question trace includes `trace_version`, creation time, provenance
fingerprints, the normalized question, estimator, proof checks, algorithm
metadata, simulation metrics, and final status. The trace audit checks that
trace files match their `manifest.json`, that provenance fingerprints agree,
that proof and simulation sections are present, and that algorithm hashes are
well-formed. The unified system audit includes this as a release gate.

Intake safety audit:

```bash
python3 -m ai_statistician.cli intake-audit --out runs/intake_audit
```

This verifies that supported external and partial question examples normalize
into registered DGP/estimator families, while unsupported examples in
`examples/unsupported_questions.json` are rejected before estimator selection,
Lean verification, or simulation. The unified system audit includes this as a
release gate.

Multi-seed evaluation:

```bash
python3 -m ai_statistician.cli eval \
  --question-file examples/questions.json \
  --n-seeds 3 \
  --runs 300 \
  --out runs/eval_external
```

This writes per-seed traces plus `evaluation_manifest.json`, with acceptance
rate, mean coverage, and mean RMSE by question.

Full proof-bank audit:

```bash
python3 -m ai_statistician.cli proof-audit --out runs/proof_audit
```

Real AXLE proof-bank audit:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli proof-audit --real-lean --out runs/proof_audit_axle
```

This writes `proof_audit_manifest.json` plus one exported Lean file per formal
obligation. The Lean exports are intentionally per-obligation files because
several examples reuse helper names such as `constantEstimator`.
It also writes `proof_attempts.jsonl` and
`proof_attempt_log_manifest.json`. Those rows are the first verifier-filtered
training substrate: they include the formal statement, spliced Lean candidate,
candidate hash, verifier, reward, errors/first error, retrieval hits, and a
`supervision_target` for successful proof bodies. This is proof-level logging
only; tactic-state transitions and process rewards remain future work.
Use `proof-training-export` to convert a checked attempt log into deterministic
whole-proof SFT data:

```bash
python3 -m ai_statistician.cli proof-training-export \
  --attempt-log runs/proof_audit/proof_attempts.jsonl \
  --out runs/proof_training_export
```

This writes `proof_sft_train.jsonl`, `proof_sft_validation.jsonl`,
`proof_sft_all.jsonl`, and `proof_training_manifest.json`. The train/validation
split is deterministic from the attempt id so reruns are comparable.
Before training a model, run the no-training whole-proof baseline:

```bash
python3 -m ai_statistician.cli proof-policy-baseline \
  --train-jsonl runs/proof_training_export/proof_sft_train.jsonl \
  --validation-jsonl runs/proof_training_export/proof_sft_validation.jsonl \
  --out runs/proof_policy_baseline
```

This nearest-neighbor proof-memory policy reports top-1/top-k exact completion
match and whether the predicted source obligation was already in the
validation example's retrieved context. It is intentionally weak; future
whole-proof SFT or rejection-sampling policies should beat it.

Retrieval audit:

```bash
python3 -m ai_statistician.cli retrieval-audit --out runs/retrieval_audit
```

This ranks each Mathlib-backed obligation against the entire local statistics
proof bank and reports top-1, top-k, and MRR. It is a premise-selection smoke
test, not a proof checker; the proof checker remains AXLE.

Optional Loogle evidence:

```bash
python3 -m ai_statistician.cli retrieval-audit \
  --loogle \
  --out runs/retrieval_audit_loogle
```

The Loogle mode calls the public Mathlib search service and stores returned
declaration names beside the local retrieval audit. It does not change the
release gate, because network search availability should not decide whether a
local build passes. The current JSON endpoint is identifier-oriented, so this is
a namespace/name-resolution smoke test for registered expected lemmas. Semantic
natural-language premise retrieval remains a Lean Finder/ReProver-style roadmap
item.

Formal source index:

```bash
python3 -m ai_statistician.cli formal-source-audit --out runs/formal_source_index
```

This is the local theorem-mining layer for proof-bank expansion. The source
inventory only checks that local formal sources exist; the formal source index
extracts Lean declaration names/signatures from Mathlib Probability/MeasureTheory,
StatInference, EmpiricalProcessLEAN, and lean-stat-learning-theory, then audits
search queries for reusable theorem families such as finite-sum variance,
Bonferroni/finite union bounds, Chebyshev tails, CLT skeletons, Borel-Cantelli,
conditional expectation, sub-Gaussian learning, empirical-process tools, and
Godambe/bootstrap algebra. The intended workflow is: index first, reuse or adapt
existing declarations second, and only then add a new AXLE proof-bank obligation.
Research benchmark traces also attach the top local declaration hits to every
`FORMAL_GAP` subclaim and copy them into the generated Lean skeleton comments,
so a gap is always accompanied by concrete local source candidates rather than
only a free-text missing-primitive label.

Algorithm registry audit:

```bash
python3 -m ai_statistician.cli algorithm-audit --out runs/algorithm_audit
```

The algorithm registry is the source of truth for executable estimators. Each
registered implementation has a stable ID, summary, version, registry status,
and SHA-256 hash of the Python source. Question traces include this metadata so
simulation reports are tied to the exact implementation that produced them.

Readiness doctor:

```bash
python3 -m ai_statistician.cli doctor --out runs/doctor
```

The doctor command is the operator preflight. It checks required runtime pieces
such as Python, `numpy`, the package directory, examples, non-empty proof and
algorithm registries, and optional production integrations such as `AXLE_API_KEY`,
the `axle` package, `ANTHROPIC_API_KEY`, the `anthropic` package, OpenProver, and
the latest run manifests. Secret values are never printed. The command writes
`doctor_manifest.json` so environment readiness can be archived next to proof,
algorithm, retrieval, and system-audit manifests.

Capability audit:

```bash
python3 -m ai_statistician.cli capability-audit --out runs/capability_audit
```

The capability audit maps the project objective to current source and manifest
evidence. It checks question intake, estimator selection, multi-agent
orchestration, AXLE-backed proof verification hooks, vetted algorithms, Monte
Carlo diagnostics, trace persistence, retrieval/prover integration, release
gates, and roadmap documentation. It intentionally marks Lean verification as
`PARTIAL`: the current system has real Mathlib-backed finite proof obligations,
but not full asymptotic statistical proofs. This makes the completion boundary
auditable instead of relying on informal claims.

Prover component audit:

```bash
python3 -m ai_statistician.cli prover-component-audit --out runs/prover_component_audit
```

The prover component audit maps the current AI Statistician system to the
AI-for-math stack in `AI for Math Resources/master_ai_for_math_formal_verification.md`:
hard verifier, formal data/autoformalization, premise retrieval, tactic/proof
policy, search/RL, subgoal decomposition, skill library, construction,
counterexample generation, simulation, provenance, and model training. This is
the honest check for whether we have actually trained/built each component.
Current expected result: verifier, benchmark data, simulation, and provenance
are release-ready; retrieval, subgoal planning, skill memory, construction,
counterexample loops, and proof-attempt logging are partial; tactic policy,
proof search, value/RL, and model training are not yet built.

Unified system audit:

```bash
python3 -m ai_statistician.cli system-audit \
  --include-partial-examples \
  --runs 300 \
  --out runs/system_audit
```

Real AXLE system audit:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli system-audit \
  --real-lean \
  --runs 200 \
  --seeds 20260528 20260529 \
  --out runs/system_audit_axle
```

This writes `system_audit_manifest.json` with release gates: algorithm audit,
retrieval audit, proof-bank audit, one-shot question runs, and optional
multi-seed evaluation. It is the release-style artifact to inspect before
trusting a build.

Release bundle:

```bash
python3 -m ai_statistician.cli release-bundle \
  --include-partial-examples \
  --runs 300 \
  --out runs/release_bundle
```

The release bundle is the top-level handoff artifact. It runs the readiness
doctor, capability audit, and unified system audit into one directory, then
writes `release_manifest.json` with a stable `release_id`, gate summary,
provenance fingerprints, counts, and paths to every sub-manifest. Use this when
you want one auditable folder that says exactly which question registry,
estimator registry, algorithm registry, and proof bank were released.

Real AXLE release bundle:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli release-bundle \
  --real-lean \
  --include-partial-examples \
  --runs 200 \
  --seeds 20260528 20260529 \
  --out runs/release_bundle_axle
```

This is the strongest current release check. It requires the real AXLE and
Anthropic-ready runtime, runs `axle.verify_proof` through the bundled proof and
question gates, and includes `real_lean_ready` in the top-level release gates.

Real Lean verification through AXLE, using the existing venv if needed:

```bash
/Users/yukang/LeanProjects/LeanPractice/.venv/bin/python \
  -m ai_statistician.cli demo --real-lean --runs 300 --out runs/axle
```

The real Lean path uses `AXLE_API_KEY` from `.env`.

## Next Production Steps

- Broaden supported estimators beyond normal means, normal variances,
  Bernoulli proportions, and constant estimators.
- Add a Loogle/Lean Finder/ReProver retrieval provider and measure cold-to-RAG
  proof lift on the local statistics proof bank.
- Add sandboxed execution before allowing any LLM-written Python algorithm into
  the registry.
- Add a Lean project for long-lived statistics definitions that should become
  Mathlib or `StatInference` contributions.
- Continue formalizing stronger statistical guarantees beyond the current
  finite-sample unbiasedness facts, then asymptotic statements only after the
  required probability theory infrastructure exists.
