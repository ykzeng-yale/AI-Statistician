# Evaluation Benchmark Strategy

Created: 2026-05-31

## Decision

Use several benchmark suites, not one larger monolithic benchmark.

The current 60-paper frontier corpus is valuable, but it is not sufficient by
itself. It mostly tests whether paper-style questions can be routed into
registered problem classes, whether traces are produced, and whether expected
theory targets are partially recovered. It does not, by itself, test full
autonomous statistical theory development, tactic-state proof search, new
formal primitive development, or safe algorithm repair.

The release audit already makes this boundary visible:

- `frontier_supported=60/60` means routing/scaffold coverage, not solved papers.
- `frontier_theory_expected_result_coverage_rate=0.855...` on the smoke set
  means theory-target recovery is useful but incomplete.
- `formal_gaps=20`, `missing_formal_primitives=97` means frontier theorem
  closure is still a formal-library development problem.
- `proofs_kernel_verified=88/88` is strong for the registered proof bank, but
  those are reusable subclaims, not complete JASA/AOAS-level asymptotic proofs.
- `proof_search_kernel_verified=12/12` is useful controller evidence, but the
  current search space is whole-proof candidate search, not tactic-state MCTS
  or trained proving.

So the right evaluation shape is a ladder: each suite isolates one capability
and exposes exactly what was proved, simulated, routed, revised, or left as a
formal gap.

## Benchmark Suites

### S0. Release Sanity Suite

Question answered: is the current scaffold internally coherent?

Primary checks:

- `pytest`
- `research-system-audit --local-lean`
- `proof-audit --local-lean`

Pass criteria:

- all unit tests pass
- all release gates pass
- proof-bank obligations are kernel verified when local Lean is requested
- trace, provenance, fingerprint, and gap manifests are internally consistent

This is a release gate, not a research benchmark.

### S1. Core Method End-to-End Suite

Question answered: can the lab run a complete trace on canonical statistical
theory tasks?

Source:

- `examples/research_questions.json`

Current shape:

- 10 canonical tasks: AIPW, split conformal, Kaplan-Meier, median-of-means,
  design-based variance, HC regression, BH FDR, anytime Bernoulli testing,
  spiked PCA, Hill/Weissman tail inference.

Pass criteria:

- every question reaches `RESEARCH_TRACE_READY_WITH_FORMAL_GAPS`
- no simulation is flagged under nominal Monte Carlo settings
- every nontrivial theorem gap is exported as a Lean skeleton
- every gap has missing primitives and local source/retrieval evidence

This tests the whole research workflow, but on curated known task families.

### S2. Frontier Static Coverage Suite

Question answered: does the intake/formalizer route frontier paper-style
questions without hallucinating unsupported capability?

Sources:

- `docs/frontier_stat_theory_benchmark.md`
- `benchmarks/frontier_stat_theory_benchmark.json`

Current shape:

- 60 DOI-backed frontier-style paper questions
- 12 topics, 5 papers each
- 23 registered problem classes represented in the latest coverage audit

Pass criteria:

- no duplicate IDs
- required fields present
- expected supported/unsupported labels are respected
- problem-class distribution is recorded and reviewed

This suite should stay mostly static so regressions are comparable.

### S3. Frontier Blind Theory-Target Suite

Question answered: given only the open question and assumptions, can the system
recover the right theorem targets?

Source:

- same 60-paper frontier corpus, but `expected_theoretical_results` and paper
  identity are withheld from the system under test

Execution:

- fast release smoke: `frontier-smoke-benchmark --max-per-class 1`
- all-supported gate: `frontier-smoke-benchmark --max-per-class 0`

Metrics:

- assumption recovery
- problem-class correctness
- expected-result semantic coverage
- theorem-goal decomposition quality
- whether the output honestly marks unsolved frontier pieces as formal gaps

Current release signal:

- smoke selected 23 questions
- 69 expected results
- 59 covered
- expected-result coverage about 85.5%

Current all-supported local signal:

- `--max-per-class 0` selects and scores all 60 frontier entries
- 180 expected results
- 149 covered
- expected-result coverage about 82.8%
- 44 traces ready with formal gaps
- 16 traces simulation-flagged
- 47 frontier-evaluation triage items: 31 theory-target misses and 16
  simulation flags

The all-supported run is intentionally stricter than the release smoke. It is a
scoring gate and limitation surfacer, not a claim that all 60 frontier problems
are cleanly solved.

Recommended next gate:

- keep 85% as the release floor for current registry-backed traces
- set 90% as the next milestone
- require per-topic coverage reporting, not only aggregate coverage
- use `--max-per-class 0` when claiming all-60 frontier theory-target coverage

### S4. Formal Primitive Ladder Suite

Question answered: are we making measurable progress from formal gaps toward
new reusable Lean statistical libraries?

Source:

- `formalization-target-audit`
- `research_gap_backlog`
- `proof_bank_expansion_export`

Current release signal:

- 97 missing formal primitives
- 74 have proof-bank plus local-source bridges
- 23 are local-source-only
- 53 have ranked proof-bank bridge candidates ready for direct reuse

Pass criteria:

- every primitive has an owning theorem goal
- every primitive has local source candidates or an explicit source gap
- bridge readiness is classified
- new proof-bank additions reduce the missing primitive count or increase
  bridge readiness

This should become the main progress benchmark for the next phase.

### S5. Proof Bank and Proof Search Suite

Question answered: can the prover stack verify known reusable subclaims and
search over proof candidates?

Sources:

- `proof-audit`
- `proof-search-audit`
- `proof-training-export`
- `proof-repair-export`
- `proof-policy-baseline`

Current release signal:

- 88/88 proof-bank obligations kernel verified in the local-kernel release
- 12/12 bounded whole-proof search obligations kernel verified in the local
  release
- proof attempts exported as SFT data

Required future upgrades:

- negative proof attempts under real Lean, not only mock/static checks
- pass@k proof sampling
- earliest-error extraction
- tactic-state traces once a Lean step environment exists

This suite is the bridge from proof-bank regression to trained prover work.

### S6. Algorithm and Simulation Stress Suite

Question answered: do vetted algorithms behave statistically under nominal and
stress data-generating processes?

Sources:

- `research-algorithm-audit`
- `research-eval`
- simulation ledgers inside research traces

Current release signal:

- 33/33 vetted research algorithms pass registry audit
- diagnostics cover bias, RMSE, coverage, FDR, power, optional-stopping error,
  PCA alignment, tail-quantile coverage, and related class-specific metrics

Needed additions:

- adversarial DGP sweeps
- wrong-algorithm negative controls
- before/after promotion tests for algorithm repair
- MC stability thresholds across seeds, not only one release run

This suite should catch empirically false theory/procedure proposals early.

### S7. Feedback Loop and Repair Suite

Question answered: does verifier or simulator feedback actually change the next
theory plan?

Sources:

- `research_loop`
- `research_loop_repair_audit`
- `research_loop_live_repair_audit`
- algorithm repair pipeline manifests

Current release signal:

- local-kernel release: `research_loop_theory_revisions=6`
- live proof-bridge artifacts are kernel verified in the release audit
- algorithm repair queues are currently empty, so that path is not stress-tested

Needed additions:

- seeded failing proof tasks that require revision
- seeded simulation failures that require algorithm or DGP diagnosis
- non-empty algorithm repair promotion examples
- before/after traces proving the repair changed a decision

This is the most important suite for claiming autonomy rather than static
workflow execution.

### S8. Adversarial and Unsupported Intake Suite

Question answered: does the system refuse tasks it cannot support and avoid
leaking gold answers?

Sources:

- `examples/research_unsupported_paper_abstracts.md`
- new adversarial frontier-style prompts

Needed cases:

- vague paper abstracts with no estimand
- contradictory assumptions
- unsupported fields such as stochastic PDE asymptotics with no registered
  surrogate
- prompts that include gold theorem text and test whether leakage controls
  separate retrieval from grading
- near-duplicate papers that should map to different theory targets

This suite protects the honesty boundary.

### S9. Fresh Holdout Frontier Suite

Question answered: does the system generalize to papers not used in templates,
retrieval cards, or benchmark curation?

Recommended source:

- periodically refreshed JASA, AOAS, Annals of Statistics, JRSSB, Biometrika,
  and Annals of Applied Statistics papers

Protocol:

- curate a small holdout set after code freeze
- withhold DOI/title from the system prompt where possible
- grade after traces are produced
- do not use holdout entries in retrieval cards, training exports, or template
  tuning until after evaluation

This is the benchmark needed before claiming progress toward a general
statistical theorist.

## Recommended Near-Term Gate

For the next development cycle, use this gate stack:

1. S0 release sanity.
2. S1 core method end-to-end.
3. S3 frontier blind theory-target scoring on all 60 entries, not only one per
   class.
4. S4 formal primitive ladder, with an explicit target to close or bridge the
   top 10 primitives.
5. S7 feedback-loop repair with at least one proof failure and one simulation
   failure that produce a verified changed trace.

Do not treat `60/60 frontier_supported` as enough. It is a routing milestone.
The next real milestone is reducing the 97 missing primitives and raising
frontier theory-target coverage while keeping all unsupported/adversarial
rejections honest.
