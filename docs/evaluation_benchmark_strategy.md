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
- `frontier_theory_expected_result_coverage_rate=0.884...` on the smoke set
  means theory-target recovery is useful but incomplete.
- `formal_gaps=20`, `missing_formal_primitives=97` means frontier theorem
  closure is still a formal-library development problem. The target/action
  audits additionally separate exact proof-bank reuse from unresolved primitive
  work; exact reuse is not new proof evidence for the full frontier theorem.
- `proofs_kernel_verified=N/N` is strong only when the cited run used AXLE or
  `--local-lean`. Release-speed `research-system-audit` runs may intentionally
  use `mock_static_check`; in that case `proofs_verified` is proof-bank
  regression evidence, not Lean-kernel evidence.
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
- release-speed audits that keep the main proof-bank audit in mock/static mode
  can pass selected `--kernel-smoke-id` obligations through local Lean; those
  rows are reported separately as `kernel_smoke_proof_audit_*` and can upgrade
  matching claim-ledger entries to kernel-backed evidence without implying the
  whole proof bank was kernel checked
- trace, provenance, fingerprint, and gap manifests are internally consistent
- `research-system-audit` gates the `claim-ledger` export so typed
  problem/procedure/theorem/proof/simulation/revision rows exist without
  collapsing simulation or retrieval support into proof evidence
- claim-ledger proof statuses report whether kernel evidence came from the trace
  verifier or from a matching `proof_audit_manifest.json` overlay
- `research-system-audit` gates `claim-ledger-action-export` so ledger evidence
  is converted into owner-agent task contracts with explicit acceptance gates

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
- 61 covered
- expected-result coverage about 88.4%

Current all-supported local signal:

- `--max-per-class 0` selects and scores all 60 frontier entries
- 180 expected results
- 151 covered
- expected-result coverage about 83.9%
- 55 traces ready with formal gaps
- 5 traces simulation-flagged
- 34 frontier-evaluation triage items: 29 theory-target misses and 5
  simulation flags
- bounded adaptive MC inside the benchmark removes the old precision-limited
  simulator-rerun queue for this smoke path

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
- `proof_bank_action_export`

Current release signal:

- 97 missing formal primitives
- exact proof-bank reuse is now reported separately from unresolved primitive
  work, so agents do not spend proof-search budget on primitives that already
  have matching verified proof-bank obligations
- 78 have proof-bank plus local-source bridges
- 19 are local-source-only
- 53 have ranked proof-bank bridge candidates ready for direct reuse
- proof-bank action export turns the candidate set into owner/priority/gate
  rows for the FormalVerifier, but those rows remain task contracts rather than
  proof evidence until AXLE/local Lean accepts the proposed proof body
- assumption primitives such as `conditional_exchangeability` are routed as
  `formalize_assumption_interface`, not as proof-bank theorem tasks. Their gate
  is a compiling, non-vacuous Lean predicate/interface plus downstream theorem
  use; the system must not close them with tautological "proofs" of the
  assumption itself.
- `assumption-interface-export` materializes those rows into Lean interface
  targets and a downstream-use theorem. A local Lean compile of that target is
  useful interface evidence, but it is still not proof evidence for the
  statistical assumption or for any downstream identification theorem.
- `formalization-delta-plan` now turns proof-bank action rows plus
  primitive-source coverage into an explicit, costed Δ-plan. This is the
  library-aware planning layer: it distinguishes exact reuse, theorem
  composition, assumption interfaces, minimal wrappers, bridge lemmas, and
  first-principles primitive work before a FormalVerifier spends proof-search
  budget. It also writes a dependency graph linking problem classes, theorem
  goals, Lean theorem skeletons, informal proof steps, imports, gaps,
  primitives, actions, stages, expected premises, proof-bank obligations, and
  candidate Lean declarations. It also emits theorem-level formalization
  routes that summarize each target skeleton's informal proof steps, required
  primitives, reuse candidates, cost class, and first next actions.
  Its cost and graph are heuristic planning evidence, not a proof of true
  minimality and not Lean proof evidence.
- `formal-verifier-queue` joins those theorem-level routes with the hard-mode
  no-registered proof-search RAG diagnostic and any selected kernel-smoke
  overlay. It ranks FormalVerifier work items by reuse/composition opportunity,
  bridge/wrapper debt, new-theory need, and observed no-registered RAG lift.
  It also attaches related proof-bank obligations, prior proof-attempt
  positives/negatives, and proof-search solved subclaim history so the next
  verifier pass can learn from earlier feedback instead of retrying routes
  blindly. The queue records graph-neighborhood dependency depth, import/source
  cone size, proof-bank/local source trust, and a lightweight semantic
  faithfulness review for each theorem route. When a selected kernel-smoke run
  verifies related proof-bank subclaims, the row records that source-trust
  calibration separately from theorem-route proof status.
  Queue rows are task contracts only; they do not become proof evidence until
  the named theorem or bridge proof passes AXLE/local Lean with a
  non-placeholder proof body.
- compose-existing bridge-chain opportunities are now 51
- minimal-wrapper debt is now 2, down from 10 after adding the robust
  median-of-means, conformal rank/quantile, and continuous-mapping wrappers

Pass criteria:

- every primitive has an owning theorem goal
- every primitive has local source candidates or an explicit source gap
- bridge readiness is classified
- every proof-bank action has a formalization-delta stage and estimated cost
- every formalization-delta plan exposes a graph with more nodes/edges than the
  flat action count, so downstream agents can traverse the route from
  problem-class theorem goals through concrete Lean skeleton declarations to
  missing primitives, existing Lean declarations, and verified bridge candidates
- every formal-verifier queue row carries an owner, required gate, proof-attempt
  mode, RAG-lift context, related proof-bank obligations, prior verifier/search
  feedback, dependency/source-trust metrics, semantic review status, and
  explicit proof-evidence boundary
- kernel-smoke overlap can calibrate source trust for related subclaims, but
  cannot close the theorem route without a non-placeholder theorem/bridge proof
- new proof-bank additions reduce the missing primitive count or increase
  bridge readiness

This should become the main progress benchmark for the next phase.

Runtime note: primitive-source coverage now defaults to
`external_search_policy=unsupported_only`. It skips external Lean/RAG searches
for primitives already backed by proof-bank bridges or local declarations, and
records both query and skip counts in the manifest. Exhaustive external-source
reuse should be evaluated with the formal-source retrieval benchmark and
retrieval ablation suites instead of inferred from primitive coverage alone.

Latest release-style scaffold signal:

- `runs/current_adaptive_mc_system_audit_v2/research_system_audit_manifest.json`
- all gates passed under local Lean kernel verification and active
  `lean_rag_dependency_graph`
- core research benchmark: 10/10 ready with gaps, 0/10 simulation flagged
- frontier smoke: 23/23 ready with gaps
- adaptive MC rerun policy resolved 4/4 precision-limited core simulations

Honesty boundary: adaptive MC reruns resolve simulator precision limitations;
they are empirical reruns, not proof evidence and not full frontier theorem
formalizations.

### S5. Proof Bank and Proof Search Suite

Question answered: can the prover stack verify known reusable subclaims and
search over proof candidates?

Sources:

- `proof-audit`
- `proof-search-audit`
- `proof-search-retrieval-ablation`
- `proof-search-retrieval-no-registered-ablation` inside
  `research-system-audit`
- `proof-training-export`
- `proof-repair-export`
- `proof-policy-baseline`

Current release signal:

- the registered proof bank is tracked by `proof-audit`; proof evidence is
  kernel-level only for runs whose `verification_strength` is AXLE or
  `local_lean_kernel_batch`
- release-speed `research-system-audit` runs can add a targeted local-kernel
  smoke overlay, for example:

  ```bash
  python3 -m ai_statistician.cli research-system-audit \
    --runs 25 \
    --lean-rag-db runs/current_status_lean_rag_dependency_graph/stat_inference.sqlite \
    --kernel-smoke-from-actions 3 \
    --kernel-smoke-id positivity \
    --kernel-smoke-id conditional_expectation \
    --kernel-smoke-id iterated_expectation \
    --lean-project /Users/yukang/LeanProjects/LeanPractice \
    --out runs/research_system_audit_kernel_smoke
  ```

  The manifest fields
  `kernel_smoke_proof_audit_total`,
  `kernel_smoke_proof_audit_kernel_verified`,
  `kernel_smoke_proof_audit_strength`, and
  `claim_ledger_kernel_overlay_upgrades` make the evidence boundary explicit.
  `--kernel-smoke-from-actions N` automatically selects up to `N` registered
  proof-bank obligations from the current proof-bank action queue, prioritizing
  exact proof-bank reuse rows before broader bridge-chain rows. The selector
  filters out Mathlib names and unregistered expected premises, so retrieval
  metadata cannot become proof evidence without a matching proof-bank
  obligation and local Lean check.
- 12/12 bounded whole-proof search obligations kernel verified in the local
  release
- proof attempts exported as SFT data

Required future upgrades:

- negative proof attempts under real Lean, not only mock/static checks
- pass@k proof sampling
- earliest-error extraction
- tactic-state traces once a Lean step environment exists

This suite is the bridge from proof-bank regression to trained prover work.
The release-safe proof-search path intentionally keeps registered proof-bank
bodies as high-priority skill-memory candidates. That is good for regression
checking, but it can saturate RAG/search ablations. `research-system-audit`
therefore runs both the ordinary retrieval ablation and a
`proof_search_retrieval_no_registered_ablation` hard-mode diagnostic with
registered proof bodies disabled. For standalone retrieval-efficiency
diagnostics, run `proof-search-audit --no-registered-proof` or
`proof-search-retrieval-ablation --no-registered-proof`, preferably with
`--local-lean`/AXLE when claiming verifier evidence. Mock/static solved counts
are not proof evidence and should not be used to claim that a new retrieval
provider proves more theorems.

Current hard-mode note: the latest `--no-registered-proof` retrieval ablation
still solves the sampled obligations at 25/25 for both baseline and enhanced
retrievers, so solved-rate lift is saturated. In that regime, report
dependency-graph activation and candidate lift as search evidence only, then
move capacity tracking to harder obligations that cannot close by static
expected-lemma templates.

`formal-verifier-queue` is the handoff from that diagnostic to theorem work:
it records whether hard-mode dependency-graph RAG increased the candidate
frontier, whether related subclaims have verifier/search history, and whether
the route has plausible source and semantic support, but keeps those signals
separate from proof status. A queue row is still unproved until AXLE/local Lean
accepts the referenced theorem or bridge proof.

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

Current pilot artifacts:

- `benchmarks/fresh_holdout_frontier_benchmark.md`
- `ai_statistician/fresh_holdout_frontier_audit.py`
- system-audit output under `runs/<audit>/fresh_holdout_frontier_audit/`

The pilot is deliberately small and should be refreshed periodically. Passing
this suite means the source-withheld traces were generated and scored; it does
not mean the system has proved the holdout papers' full theorems in Lean.

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
