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
- Current release proof-bank evidence is `proofs_kernel_verified=126/126`.
  This is strong only when the cited run used AXLE or
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
- component-resource registry and publication-bundle audits validate planner
  execution-plan rows and resource request/response contract rows against the
  published reusable JSON Schemas, so local-first/frontier escalation contracts
  and frontier-tool/prover-resource contracts cannot silently drift from the
  publication bundle
- `research-system-audit` exposes the planner's reusable handoff contracts in
  its artifact map, including the route-replan standalone seed schema, the
  cross-prover target summary and schema, and the publication-bundle schema
  catalog and schema; its counts also report target-summary contract errors and
  schema-catalog validity so these reusable contracts can be release-gated
- action-resource plans validate one local-first/frontier-escalation resource
  plan per primitive action, so release audits can see which concrete
  literature, formal-library, MCP/LSP, prover-feedback, and cross-prover
  resources each primitive work order is allowed to use
- resource-request queues validate one dispatch packet per selected
  local-first or frontier resource, so release audits can see which executable
  request, contract fields, acceptance gate, and adapter/MCP hint will be used
  before any tool response is treated as evidence
- resource-response ledgers validate local/frontier tool outputs against those
  request packets, record missing responses as awaiting work, and reject
  malformed responses or `kernel_verified=true` claims before feedback can
  revise a route
- the planner library-coverage map validates one row per selected route
  primitive against a published schema, so release audits can see whether the
  current library coverage is exact reuse, near reuse, wrapper work, bridge
  work, source-port work, new theory, or unknown alignment
- LLM route-planner standalone seeds publish a deterministic route-selection
  summary across accepted candidates, ranking first by route-adoption readiness
  and then by minimal-delta route cost, blocker count, and original request
  order; this keeps replay focused on the cheapest source-backed extension
  rather than whichever valid LLM response happened to arrive first, and
  standalone/reuse-smoke manifests plus publication-bundle audits report and
  validate the selected rank and minimal-delta cost trace
- claim-ledger proof statuses report whether kernel evidence came from the trace
  verifier or from a matching `proof_audit_manifest.json` overlay
- claim-ledger formal gaps can also be upgraded by a matching
  `formal_verifier_replay_repair_patch_response_promotion_manifest.json`, but
  only when the promotion row is already ready, kernel verified, and backed by
  replay attempt/calibration evidence
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
  proof evidence until AXLE/local Lean accepts the proposed proof body. Within
  tied priority-score groups, it now publishes a
  `proof_bank_action_source_aware_rerank_policy` and prefers exact verified
  proof-bank obligations, ranked proof-bank bridge obligations, and local
  Mathlib/StatInference/AIStatistician declarations while demoting WIP,
  sorry/admit, axiom, unsafe, or unverified candidate evidence.
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
- `formal-verifier-replay-export` turns those ranked queue rows into concrete
  route-level replay tasks and replay-policy training examples. It chooses
  modes such as kernel-calibrated subclaim replay, proof-search subclaim replay,
  bridge-lemma replay, semantic route review, or theorem-composition replay.
  The artifact is useful for telling the FormalVerifier exactly what to replay
  next and which acceptance gate to preserve, but it is still not proof
  evidence. Subclaim replay and kernel-smoke overlap calibrate only related
  obligations; the theorem route closes only after the replay target passes
  AXLE/local Lean with a non-placeholder proof.
- `formal-verifier-replay-attempts` is the execution layer for those tasks. It
  can consume formal-gap Lean task skeletons, strip the `h_frontier_missing_*`
  placeholder assumption from the theorem target, run a non-placeholder replay
  proof body through the selected verifier, and write full-route attempt JSONL.
  Failed attempts are useful Lean/AXLE repair feedback. Positive mock/static
  attempts are not proof evidence; only kernel-verified attempts with the
  placeholder removed can close a replay target.
- `formal-verifier-replay-calibration` records what happened after those replay
  tasks were attempted. With no full-route attempt log, it marks every replay
  target as `awaiting_full_route_attempt`. With an attempt log, it separates
  failed full-route attempts, non-kernel positives that require AXLE/local Lean
  replay, and genuinely kernel-verified full theorem/bridge targets. This is
  the first full-route feedback ledger for replay policy repair; only
  `full_route_kernel_verified` rows are proof evidence.
- `formal-verifier-replay-repair-export` turns failed calibrated replay attempts
  into route-specific repair packets. The packet joins the failed Lean/AXLE
  error, replay-task subclaim obligations, attempt retrieval hits, and a
  candidate bridge/import/type-alignment repair plan. These packets and their
  proof-body templates are not proof evidence; they are accepted only after the
  repaired route is rerun through AXLE/local Lean and calibrates as
  `full_route_kernel_verified`.
- `formal-verifier-replay-repair-application-export` turns those repair packets
  into per-route Lean repair scaffolds and rerun-command tasks. The scaffolds
  point at the candidate bridge/import/type repair and the failed
  placeholder-stripped target, but they are still work artifacts only; evidence
  begins after the repaired route is rerun and kernel calibrated.
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
- every formal-verifier replay task carries a replay mode, replay steps,
  subclaim replay obligations, training prompt/completion, acceptance gate, and
  proof-evidence boundary
- every formal-verifier replay attempt strips placeholder assumptions from
  matched formal-gap skeletons before verification and records verifier
  outcome, first error, placeholder-removal status, and kernel evidence status
- every formal-verifier replay calibration row carries attempted/awaiting
  status, first-error category when available, repair-policy update, and a
  proof-evidence boundary that accepts only full-route kernel verification
- every formal-verifier repair response validation row records whether a worker
  response is awaiting, a non-evidence patch proposal, an accepted
  full-route-kernel proof artifact, or a rejected unsupported proof claim
- every formal-verifier repair response promotion row records whether a
  validated response is awaiting, needs replay calibration, is blocked by
  evidence-manifest mismatch, or is ready for proof-ledger promotion
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
- `formal-verifier-replay-repair-application-validation` checks generated
  repair scaffold files for source-artifact integrity and optional local Lean
  compilation, but this remains non-evidence until a repaired full-route replay
  attempt calibrates as `full_route_kernel_verified`
- `formal-verifier-replay-repair-execution-queue` ranks validated repair
  scaffolds into prover/RAG patch work orders with rerun commands and explicit
  promotion gates; queue rows are still not proof evidence
- `formal-verifier-replay-repair-prompt-packets` packages ready repair work
  orders into self-contained prover/RAG prompts with scaffold source, output
  contracts, forbidden proof claims, and replay-calibration gates
- `formal-verifier-replay-repair-patch-autoworker` answers those prompt packets
  with conservative local patch proposals and patched scaffold artifacts; these
  responses keep `kernel_verified=false` until replay attempts and calibration
  produce full-route kernel evidence
- `formal-verifier-replay-repair-patch-response-validation` validates worker
  patch responses against those contracts. Absent responses are awaiting work,
  patch proposals remain non-evidence, and proof evidence is accepted only for
  full-route kernel-verified calibration with no residual formal gaps.
- `formal-verifier-replay-repair-patch-response-promotion` exports
  proof-ledger promotion rows from validated responses, but only accepted
  full-route kernel responses with corroborating replay attempt and calibration
  manifests become promotion-ready
- `formal-verifier-replay-repair-patch-rerun-queue` carries patch proposals that
  still need replay calibration into typed rerun work items with artifact,
  command, and promotion-gate context; these rows are not proof evidence
- `formal-verifier-replay-repair-patch-rerun-attempts` runs queued patch
  artifacts through local Lean source checks when configured; a compiling patch
  artifact is source-artifact evidence, not theorem proof evidence
- `formal-verifier-replay-repair-patch-rerun-calibration` separates compiling
  patch proposals from `full_route_kernel_verified` reruns before any
  proof-ledger promotion path can consume them
- `formal-verifier-replay-repair-patch-rerun-residual-obligations` decomposes
  unverified calibrated patch reruns into primitive-level proof/library work
  items, joined with primitive-source coverage and proof-bank action metadata
- `claim-ledger --repair-response-promotion-manifest` applies those ready rows
  as a question-scoped overlay to the matching formal gap; non-ready rows remain
  task/queue state and do not close ledger proof gaps
- `lean-rag-dependency-health` records schema, integrity, and FTS-probe status
  for the optional dependency-graph DB; malformed DBs are disabled with a
  fallback reason instead of crashing the audit
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
`proof-training-export` now publishes source-aware training promotion sidecars
beside the compatibility SFT files: kernel-verified clean positives are copied
to `proof_sft_source_aware_*`, non-kernel or source-risk positives are copied to
`proof_sft_quarantined_positive.jsonl`, and failed attempts are copied to
`proof_sft_hard_negatives.jsonl`. This lets publication-grade training runs
avoid mock/static or WIP/sorry-heavy positives while keeping those traces
available for review, theorem-shape planning, and repair/value datasets. The
same export writes `proof_premise_feedback.jsonl`: successful expected lemmas
are positive premise labels, retrieved-but-unused hits from successful attempts
are hard negatives, and retrieval hits from failed attempts are hard negatives.
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

Recent agentic-prover integration: residual follow-up rows now feed a
`formal_verifier_agentic_proof_strategy_plan` gate. The plan borrows the useful
architecture from Ax-Prover, AlphaProof Nexus, and AlphaEvolve: verifier-driven
Lean proof-state loops, proof-sketch/global-goal-cache reuse, and scoped
evolve-block candidate evaluation. It reports patch-evolve and source-discovery
cache work as search plans only; promotion still requires local Lean/kernel
calibration and residual-gap validation.
The follow-on `formal_verifier_agentic_proof_candidate_evaluation_queue` gate
adds candidate database lineage, attempt budgets, evaluator pools, live-tool
sequences, and promotion gates, turning those plans into auditable work orders
for proof-candidate generation without upgrading them to proof evidence.
The reusable LLM route-payload validator now treats ready strategy-plan rows as
request-bound obligations: each ready row must be answered by a matching
source-search, planner-next-action, or formal-attempt item before the response
can be accepted. This makes ignored proof-search plans measurable in benchmark
artifacts through strategy-row, ready-row, and obligation-error counters without
conflating those counters with kernel proof evidence.
The `formal_verifier_agentic_proof_safety_policy` gate adds bounded edit
markers, declaration/header guards, forbidden-token checks, helper-lemma
anti-restatement checks, source-claim checks, goal-cache keys, and SafeVerify
promotion requirements before candidate generation can be treated as a valid
work order.
The `formal_verifier_agentic_proof_attempt_population` gate then registers
safety-gated work orders into reusable proof-search memory with goal-cache
keys, candidate lineage, proof-sketch population keys, untried diagnostic
signatures, lessons learned, and sampling weights. Those population scores are
search signals only, not proof evidence.

The `goal_conditioned_minimal_formalization_plan` gate is the complementary
efficiency layer before replay: it converts the global formalization delta and
verifier queue into theorem-specific minimal cuts, including selected
primitives, exact-reuse/wrapper/bridge/source nodes, next worker packets, and
`do_not_formalize_now` hints. It should reduce wasted formalization breadth,
but it is still route-selection metadata rather than theorem proof evidence.
The `formalization-gap-planner-evaluation` gate scores those route selections
against held-out or curated route truth with route recall/precision,
formalization-delta precision/recall, existing-reuse precision/recall, coverage-label
accuracy, residual/side-condition primitive precision/recall, two-DAG
readiness, feedback-loop readiness, and LLM cost-tier decision traces. The
evaluation rows expose model-tier decision basis, Sonnet trigger counts, and
source-theorem/proof-body feedback counts, so benchmarks can separate cheap
bounded Haiku triage from Sonnet calls justified by semantic primitive gaps,
proof-body execution failures, or formal-environment blockers. LLM planner
request packets also expose normalized target-prover-family distributions and
resource-feedback readiness counters, so evaluation can check whether
feedback-driven replans preserve low-delta reuse priorities for each prover
family instead of expanding into avoidable source ports or new theory. Route-truth files may provide
`expected_residual_primitives` and `expected_residual_goals` so proof-state
feedback can be scored as a bounded oracle signal rather than treated as a
binary success flag. It publishes an evaluation-row JSON Schema and row
schema-valid counts so these diagnostics can be compared outside the AI
Statistician codebase. These are planner benchmark scores; they do not replace
kernel verification.
The `formalization-gap-planner-benchmark-audit` gate validates the route-truth
benchmark before it is used as publication evidence: it checks source-reference
coverage, theorem-family diversity, primitive accounting, coverage labels,
public/held-out split metadata, route-row schema validity, and proof-boundary
text. It is dataset-quality evidence for the planner benchmark, not theorem
proof evidence.
The `formalization-gap-planner-ablation-study` gate compares the full recorded
planner against no-literature, no-formal-grounding, no-proof-state-feedback, and
no-route-planner counterfactuals. It reports route/delta recall drops, reuse
loss, residual-recall loss, and feedback readiness loss as planner diagnostics;
it does not prove any theorem.
The `formalization-gap-planner-target-intake` command is the public first
stage for raw theorem requests: it normalizes objects, assumptions, procedure,
claim, theorem shape, source refs, primitive seeds, and
literature/formal-library queries before standalone planning. The emitted JSONL
rows have a published target-intake row schema for external validation, but
they are route seeds only;
they must be upgraded through literature evidence, library grounding, and
prover feedback before any proof-route claim.
The `formalization-gap-planner-llm-route-planner` gate is the explicit
LLM/agent intelligence path for that upgrade. It builds a target theorem
context packet containing the current route, optional source-grounding rows,
library-coverage rows, resource-response/prover residuals, the required JSON
output contract, and the proof boundary. It also exports those compact target
theorem context packets as JSONL plus schema, so benchmark consumers can audit
the normalized theorem statement, assumptions, source refs, primitive
candidates, residual counts, and target prover family without reparsing the
full prompt packet. Prompt-only runs are valid staging
artifacts. Reviewed/static or live-provider responses are accepted only when
they include source-grounded informal DAG nodes, Lean/formal realization DAG
nodes, informal-to-formal alignment rationales, minimal-delta rationale,
bounded search requests or uncertainty flags when evidence is weak, and an
explicit `not theorem proof evidence` boundary. Any `kernel_verified=true`
claim is rejected before the response can become a standalone route seed.
For live-provider runs, the LLM route-planner manifest reports
`provider_usage_rows` plus aggregate input/output/cache/total token counters by
provider, model, and model tier. Evaluation rows and summaries preserve these
as cost-control
metadata for Haiku/Sonnet routing, separate from source, library, prover, and
kernel evidence. Reuse-smoke and publication-bundle summaries lift the same
provider-usage totals for the primary and feedback route-planner passes, and
add a combined provider-usage rollup so benchmark tables can compare route
quality and Claude tier cost from one reusable artifact.
The `formalization-gap-planner-portable-plan-audit` gate validates the plan
contract before any scoring or target-prover mapping: schema identity, library
snapshot consistency, two-DAG and AND/OR structure, work-packet gates,
interactive hooks, and the absence of kernel-proof claims in the planning
layer. It also reports audit-row schema-valid counts and writes
`formalization_gap_planner_portable_plan_audit_row.schema.json`, so a benchmark
consumer can reject malformed audit JSONL before using the diagnostics.
The `formalization-gap-planner-library-coverage-map` gate exports the compact
per-primitive library coverage view from the same portable plan. It records
which selected route primitives are exact current-library reuse, near reuse,
wrapper work, bridge lemmas, source ports, new theory, or unknown/unaligned,
records the manifest-level `by_target_prover_family` distribution for the
coverage rows, and validates those rows against
`formalization_gap_planner_library_coverage_map_row.schema.json`. This is a
library-alignment planning artifact, not proof evidence.
Publication bundles lift the same target-family distribution into
`library_coverage_map_summary`, so public benchmark artifacts expose the
coverage scope without requiring consumers to inspect the nested coverage-map
manifest first. The publication-bundle audit recomputes that summary from the
copied coverage-map manifest and JSONL rows, rejecting stale target-family
coverage claims.
The `formalization-gap-planner-primitive-action-queue` gate consumes that
coverage map and emits one executable primitive work order per selected route
primitive. Its row schema records the action kind, owner, priority, required
inputs, expected outputs, recommended tools, acceptance gate, and reproduction
commands for target-prover replay, composition, wrappers, bridge lemmas, source
ports, new theory fragments, or rerunning library alignment. This is the
planner's primitive-level work queue and remains not proof evidence. Within a
fixed minimal-delta class, the queue also publishes and applies a
`source_aware_rerank_policy`: importable/local verified candidate declarations
are preferred, while WIP, sorry/admit, axiom, unsafe, or unverified declaration
evidence is demoted before prover work is scheduled.
The `formalization-gap-planner-action-resource-plan` gate joins those primitive
work orders to the component-resource registry. It validates that each queued
action has planner component ids, local-first resources, frontier escalation
resources, adapter ids, resource-contract ids, request/response contract
fields, escalation triggers, stop conditions, and reproduction commands under
`formalization_gap_planner_action_resource_plan_row.schema.json`. This is the
resource-aware execution surface for frontier tools and MCP/prover adapters; it
is not theorem proof evidence.
The `formalization-gap-planner-resource-request-queue` gate expands each
action-resource plan into per-resource request rows. It validates request
phase, resource id, action/route identifiers, contract fields, request payload,
expected response artifact, execution hint, structured dispatch spec, and
proof-boundary discipline under
`formalization_gap_planner_resource_request_queue_row.schema.json`. This is the
adapter dispatch surface for literature, formal-library, prover-feedback,
route-revision, and cross-prover resources; the nested `request_payload`
includes the generated `resource_request_id`, request rank, expected response
artifact, response-contract fields, and dispatch spec needed for an external
MCP/CLI adapter to emit a valid response row. LLM route-planner follow-up rows
also include `llm_route_planner_query_intents`, a structured query inventory
over primitive names, theorem goals, problem classes, gap reasons, candidate
bridge/source-port work items, and target retrieval surfaces. It is not theorem
proof evidence.
For LLM route-planner follow-ups, the manifest also reports route-adoption
precondition rows, blockers, required response fields, target primitives, copied
request packets, and copied request-payload target scopes, so benchmark traces
can detect a formal-attempt or route-adoption blocker becoming unscoped before
dispatch.
The `formalization-gap-planner-resource-response-ledger` gate validates
local-first and frontier responses keyed by those request rows. It records
matched/missing response-contract fields, source refs, Lean declaration hits,
coverage updates, prover diagnostics, residual goals, and route-revision
recommendations under
`formalization_gap_planner_resource_response_ledger_row.schema.json`. Missing
responses are `AWAITING_RESOURCE_RESPONSE`, not a failed gate, while malformed
responses and `kernel_verified=true` claims are rejected in this non-proof
layer. Ledger rows retain the request `dispatch_spec`, so downstream feedback
can still be audited against the exact adapter surface that was requested. They
also retain queued minimal-delta cost, reuse/evidence readiness, and priority
rationale fields, so route repair remains accountable to the original
library-reuse preference after resource responses arrive asynchronously.
Responses that echo a different resource, expected artifact, or dispatch spec
are rejected as request mismatches rather than accepted as planner feedback.
Accepted ledger rows with source, library, coverage, residual-goal, or
diagnostic feedback are consumed by `formalization-gap-planner-route-revision-overlay`
as conservative non-proof proposals. The overlay also records compact
`applied_resource_response_traces`, including that dispatch and readiness
context, so the
accepted response row can be audited after it becomes route-revision state,
while missing and rejected responses remain explicit capacity or contract gaps
through per-route resource-response status summaries.
The LLM route planner uses the same boundary in its prompt contract: accepted
ledger or refinement-evidence feedback may guide residual interpretations,
search requests, planner actions, or formal-attempt items only when available
ledger/evidence ids, resource request ids, target primitives, source
refs/snippets, and prover diagnostic provenance are preserved.
The `formalization-gap-planner-minimal-delta-audit` gate separately checks the
planner's minimal formalization-delta discipline: cost arithmetic, selected cut versus
work packets, `do_not_formalize_now` exclusions, AND/OR connectivity for delta
nodes, route ordering, and obvious same-target dominance. It is a structural
minimality proxy, not a proof of true semantic optimality. It also exports a
minimal-delta decision JSONL and schema so paper supplements can expose the
costed cut, excluded primitives, dominance status, and proof-boundary state per
route without requiring AI Statistician internals.
The `formalization-gap-planner-source-grounding-audit` gate checks every
informal route-DAG node for attached source refs, an explicit formal-gap
boundary, or a bounded literature-discovery obligation. It is source-discipline
evidence, not proof evidence. It also exports a source-grounding row schema and
schema-valid counts for those per-node grounding rows. After proof-state
feedback is available, the same gate can consume the refinement-evidence
manifest and add residual-source rows for prover residual goals. This makes
side conditions learned from Lean measurable as source-backed,
source-search-pending, formal-boundary-declared, or unaccounted before they are
allowed to drive route repair.
The `formalization-gap-planner-reuse-smoke` gate composes the public path for
independent reuse: target intake, standalone planning, portable-plan audit,
library-coverage map, minimal-delta audit, source-grounding audit,
prover-adapter contract export, adapter-registry export/audit,
component-resource registry/audit,
deterministic refinement responses, local literature/formal-source/proof-state
adapter fallbacks, evidence/overlay/stability/replan/triage exercise,
cross-prover matrix audit, publication bundle with its route-truth benchmark
audit, and bundle audit. It is a reproduction/packaging smoke test for paper
supplements and non-Lean prover adapters, not proof evidence. Its manifest
also reports source-registry and packaged-bundle component-resource component
row, resource row, execution-plan row, adapter-registry row, source and packaged
prover-adapter packet schema-valid counts, and refinement work-item,
deterministic refinement-adapter response, refinement tool-response,
refinement evidence row, proof-state triage row, local-adapter response,
route-alignment edge, interactive next-action row,
interactive decision-policy row, source-grounding row, benchmark route row,
optional evaluation row, route-revision overlay row, route-stability audit row,
route-replan handoff row, handoff-audit row, ablation-study row,
component-resource contract row, prover-adapter response schema artifact path,
prover-adapter response-validation row,
library-coverage map row, cross-prover matrix row, cross-prover packet row, and
cross-prover response-validation row schema-valid counts, plus cross-prover
target-summary contract errors, target-summary artifact paths, publication
bundle schema-catalog entry counts, schema-catalog contract errors, and
schema-catalog artifact paths,
and the bundle audit revalidates packaged optional target-intake rows against
the published target-intake row schema, standalone seeds, goal-plan rows against
the published gap-plan row schema, minimal-delta decision rows,
source-grounding rows, refinement work-item rows, adapter-registry audit
checks, and component-resource-registry audit checks against their public
contracts or schemas,
so external users can see whether the local-first/frontier-escalation contract,
frontier-tool request/response contracts, two-DAG alignment contract,
interactive route-action contract, route-revision/replan contracts, and
target-prover packet and response-validation contracts survived the full public
path.
The `formalization-gap-planner-adapter-registry` gate records the intended
frontier adapters for each refinement hook and their local readiness:
Paperclip/PaperQA/OpenScholar-style literature search, LeanSearch/Loogle/
LeanExplore/local Lean RAG grounding, Lean/LSP and LeanDojo-style proof-state
feedback, and the built-in route-revision overlay. Missing commands,
credentials, or configured paths are capacity gaps, not proof failures.
The `formalization-gap-planner-adapter-registry-audit` gate makes that inventory
testable for publication: it checks required frontier adapters, hook coverage,
response fields, resource links, prover-family portability, adapter-row JSONL
schema conformance, and proof-boundary discipline.
The `formalization-gap-planner-component-resource-registry` gate records the
architecture-level mapping from planner components to local fallbacks and
frontier resources/MCPs: Paperclip/PaperQA/OpenScholar for literature,
dependency-graph/blueprint methods for informal DAGs, LeanSearch/Loogle/
LeanExplore/local Lean RAG for library grounding, Lean/LSP/LeanDojo and
cross-prover Rocq/Isabelle/Agda interfaces for proof feedback, and publication
bundle/cross-prover audits for reuse. Its audit verifies that every component
has coverage, contract fields, resource links, and proof-boundary discipline.
It also validates per-resource `capability_tags` and `validation_signals`,
per-component `required_quality_signals`, per-execution-plan `quality_gates`,
and per-resource-contract `response_validation_signals`. These are the
evaluation-facing checks that decide whether local evidence is good enough or
whether a Paperclip/PaperQA/OpenScholar, LeanSearch/Loogle/LeanExplore,
Lean/LSP, or cross-prover resource should be escalated.
The `formalization-gap-planner-local-literature-adapter` gate is the
live-local literature fallback behind that registry: it replaces offline
`literature_discovery` rows with source refs and route-evidence nodes from a
local text/markdown/json corpus, or emits focused literature-gap nodes when no
local source matches. These rows are source-route evidence only.
The `formalization-gap-planner-local-formal-source-adapter` gate is the first
live-local grounding adapter behind that registry: it replaces offline
`lean_library_grounding` rows with declaration hits and coverage updates from
the current formal-source retriever, optionally fused with the Lean RAG
dependency graph. These hits are library-grounding evidence only.
The `formalization-gap-planner-local-proof-state-adapter` gate is the
corresponding local prover-feedback adapter: it consumes queued
`proof_state_feedback` skeletons, runs local Lean when available, blocks
`sorry`/`admit`/`axiom` probes before invocation, classifies name-only
non-Lean skeletons as statement-materialization gaps, and records diagnostics
plus residual goals for route revision. These rows are proof-state diagnostics
only, not theorem proof evidence.
The `formalization-gap-planner-refinement-queue` gate then turns route
revision triggers, interactive hooks, evaluator mismatches, and replay
calibration residuals into bounded work items for literature discovery,
Lean-library grounding, proof-state feedback, and route-DAG revision. This is
the executable interface to frontier tools such as Paperclip/PaperQA/OpenScholar,
LeanSearch/Loogle/local Lean RAG, and Lean/LSP/prover feedback.
The `formalization-gap-planner-refinement-adapter-responses` gate provides a
deterministic local adapter over the route-truth benchmark labels so this
interface can be regression-tested without live MCP credentials. Its JSONL
responses are then validated by `formalization-gap-planner-refinement-evidence`;
they remain route-revision evidence, not theorem proof evidence.
The `formalization-gap-planner-route-revision-overlay` gate then applies those
accepted proposals, plus accepted resource-response ledger feedback when a
ledger directory is supplied, back to the current route plan as a non-mutating
overlay. This makes the reflect-and-revise step inspectable before rerunning
planning and replay. The overlay records changed primitives and DAG nodes, and
also carries compact resource-response status summaries so awaiting or rejected
resource outputs can affect stop/expand decisions without being accepted as
route-revision proposals. It still does not close any proof obligation.
The `formalization-gap-planner-route-stability-audit` gate consumes the plan,
refinement evidence, and route overlay to decide whether each route has
stabilized under the current evidence bound or should expand literature search,
Lean-library grounding, proof-state feedback, resource-response execution or
repair, or route replanning. Awaiting and rejected resource-response request
ids are preserved on the stability rows so interactive sessions can name the
specific external adapter requests to run or repair. Route-adoption
precondition rows also preserve their target primitive scope, so a blocked or
unresolved precondition remains tied to the informal theorem objects that need
more source, library, or proof-state evidence. A route that needs expansion can
still be a valid audit row; stability is a stop/expand planning decision, not
theorem proof evidence.
The `formalization-gap-planner-route-replan-handoff` gate converts route
overlays and stability decisions into a replayable standalone seed for the next
planner round. It preserves revised informal DAG nodes, revised
Lean-realization DAG nodes, and exact revised route-alignment edges in the
handoff rows, each seed route, and the seed route metadata so a downloaded
bundle can audit continuity from informal route nodes to formal realization
candidates. It also preserves applied proposal ids, evidence ids, hook kinds,
compact resource-response traces, pending or rejected resource-response
request ids, prover-attempt statuses, diagnostic signatures, residual goals,
source refs, and Lean declaration hits so resource-response-ledger feedback
reaches the next route synthesis pass. It
also writes the standalone-input schema beside the seed so the replan handoff
is a self-describing input contract for external planner reruns; that schema
publishes the optional replan metadata fields for revised DAG nodes, alignment
edges, applied feedback ids, applied response traces, diagnostics, source refs,
and Lean declaration hits. The standalone planner copies that seed
provenance into roundtrip goal-plan rows as `standalone_input_trace`, giving
external prover queues a stable way to recover overlay/resource/prover-feedback
context after replanning. It is a
feedback-loop handoff, not proof evidence.
The `formalization-gap-planner-route-replan-handoff-audit` gate validates that
handoff after export or download, checks that the standalone seed has no
promoted kernel-proof claim, verifies the standalone seed schema id, verifies
preserved selected-primitive alignment, checks exact row-to-seed preservation
of revised DAG and alignment payloads, checks row-to-seed provenance
continuity, and reruns the standalone planner on the seed to ensure alignment
is regenerated and `standalone_input_trace` survives. The audit also reports
roundtrip route-adoption-precondition target primitive counts so scoped
pre-response blockers remain visible after replay. It is replayability
evidence, not theorem proof evidence.
The `formalization-gap-planner-proof-state-triage` gate ranks route-overlay
prover statuses into next work items such as non-placeholder theorem
materialization, local Lean repair, or environment configuration. It is an
operational proof-worker handoff, not proof evidence.
The `formalization-gap-planner-interactive-session` gate then joins the current
plan, refinement queue, evidence rows, stability decisions, replan handoff, and
proof-state triage into one per-route next-action ledger. It tells the
orchestrator whether to run bounded literature search, Lean grounding,
proof-state feedback, route replanning, or target-prover replay next. It also
emits decision-policy rows that record trigger signals, evidence inputs,
required tool contracts, component/resource ids, required quality signals,
quality gates, response-validation signals, stop conditions, and fallback
actions for each next action. Its row schema preserves and validates scoped
route-adoption-precondition target primitive counts, so unresolved pre-response
obligations stay tied to the theorem primitives they block. These are session
orchestration evidence only.
The ablation study can consume that session ledger to quantify what is lost
when proof-state feedback is unavailable, while keeping route-quality evidence
separate from kernel proof status.
The `formalization-gap-planner-prover-adapter-contract` gate turns portable
work packets into target-prover mapping tasks for Lean, Rocq/Coq, Isabelle,
Agda, or another prover family. It validates translated statements, imports,
verifier commands, library snapshot refs, and residual translation gaps, but it
rejects `kernel_verified=true` claims because proof status belongs to a
separate target-prover replay/calibration gate. It exports schema-valid counts
for both packet rows and response-validation rows. Adapter packet provenance is
target-aware: every generated `standalone_input_trace` records the source prover
family, the source route target family, the adapter target prover family, and
the target library snapshot; packet validation rejects trace/packet target
mismatches.
The `formalization-gap-planner-cross-prover-matrix-audit` gate reruns that
packet export for Lean4, Rocq, Isabelle, and Agda from the same portable plan,
checks packet-count consistency, verifies that every target packet still carries
route-alignment evidence and nonempty `standalone_input_trace` provenance,
checks rejection counts, and writes aggregate packet/validation JSONL for
external prover teams. It also validates matrix rows, aggregated packet rows,
aggregated response-validation rows, and a target-summary JSON artifact against
published schemas. The target summary tells a downstream prover team which
filter value to use in the aggregate packet and validation JSONL for its prover
family, and exposes standalone-trace and replan-metadata trace counts. It is
portability evidence, not proof evidence.
The `formalization-gap-planner-publication-bundle` gate packages the portable
schema, contract, benchmark, benchmark audit, adapter registry, docs, and
optional run artifacts, including the source-grounding row schema contract,
component-resource component/resource row contracts, benchmark route-row
contract, evaluation row contract, refinement tool-response contract,
refinement evidence-row contract, route-stability audit-row contract,
route-replan handoff-audit row contract, portable-plan audit-row contract,
library-coverage map row contract, primitive-action queue row contract,
action-resource plan row contract, resource-request queue row contract,
resource-response contract, resource-response-ledger row contract,
ablation-study row contract,
proof-state triage-row contract,
prover-adapter response-validation row
contract, cross-prover matrix-row contract, cross-prover target-summary
contract, component-resource resource-contract row contract, and execution-plan
contract into a reusable supplement. This is the artifact to
cite or hand to a
non-Lean prover adapter. It includes a `reproduce/` manifest listing
bundle-relative artifacts and commands for auditing the bundle, running the
standalone planner, auditing a plan, exporting target-prover work packets,
running the refinement loop, rerunning route-replan handoff, auditing that
handoff, and triaging proof-state feedback; it also includes runnable
standalone and target-intake example JSON files. It also includes
`contract/formalization_gap_planner_schema_catalog.json`, a machine-readable
index of the reusable schema and contract files, with a reusable
`validate_schema_catalog_payload()` contract validator. It is not theorem proof
evidence.
The `formalization-gap-planner-publication-bundle-audit` gate validates that
supplement after export or download: required files exist, schema ids match,
the benchmark, benchmark audit, adapter registry, reproduction manifest, and
example inputs are usable, benchmark route rows satisfy the published route-row
schema, optional evaluation rows satisfy the published evaluation-row schema,
optional refinement evidence rows satisfy the published evidence-row schema,
optional deterministic refinement-adapter responses satisfy the shared
refinement-tool response schema,
optional local literature/formal-source/proof-state adapter responses satisfy
the shared refinement-tool response schema,
optional route-revision overlay rows satisfy the published overlay-row schema
and preserve alignment/resource-response-ledger proposal counts plus
ledger-derived resource-response status summaries,
optional route-stability rows satisfy the published stability-row schema and
their awaiting/rejected resource-response decisions and scoped
route-adoption-precondition target primitives agree with the packaged overlay
status summaries,
optional route-replan handoff rows satisfy the published handoff-row schema,
optional route-replan handoff-audit rows satisfy the published audit-row
schema, optional route-replan standalone seed schemas carry the published
standalone-input schema id, optional route-replan standalone seeds exactly
preserve revised alignment edges and revised informal/Lean DAG nodes from the
packaged handoff rows, optional route-replan standalone seed schemas expose
the replan metadata contract, optional handoff-audit rows include a passing
roundtrip standalone-input trace check and a passing LLM route-planner
hook-trace preservation check, optional portable-plan audit rows satisfy the
published audit-row schema, optional library-coverage map rows satisfy the published coverage-map
row schema, optional primitive action-queue rows satisfy the published work-queue
schema, optional action-resource plan rows satisfy the published resource-plan
schema, optional resource-request queue rows satisfy the published request
schema, optional resource-response ledger rows satisfy the published
response-ledger row schema, optional ablation-study rows satisfy the published
ablation-row schema,
optional proof-state triage rows satisfy the published triage-row schema,
prover-adapter response schemas carry the published schema id,
optional prover-adapter response-validation and cross-prover matrix rows
satisfy their published schemas,
the schema catalog has the expected schema id and resolves to bundle-local
contract/schema files,
optional artifacts stay inside the bundle, optional route-replan handoff
artifacts preserve and roundtrip alignment edges, packaged handoff rows preserve
revised DAG/alignment payloads, pending or rejected resource-response request
ids, and applied-hook/evidence/prover/source/declaration provenance into the
standalone seed metadata, packaged handoff audits include a passing row-to-seed
provenance check, and proof-boundary text remains intact.

The `formalization-gap-planner-component-resource-registry` gate is also a
reproducibility surface: beyond listing resources, it emits one execution-plan
row per planner component with local-first resources, frontier escalation
resources, adapter ids, evidence inputs, expected outputs, escalation triggers,
and stop conditions. It also emits one resource-contract row per local
fallback, frontier tool, MCP surface, or prover resource with request fields,
response fields, deployment requirements, output artifact kind, escalation
policy, and acceptance gate. The corresponding audit requires those execution
plans and resource contracts to resolve to known resources and preserve
proof-boundary discipline. Publication bundles include JSON Schemas for the
execution-plan and resource-contract row formats so external systems can
validate this local-first/frontier-escalation and tool-contract surface.
The action-resource plan gate then materializes that surface per primitive
work order, which lets evaluations count whether bridge lemmas, source ports,
wrappers, and target-prover replay actions all have concrete local-first,
frontier-escalation, and resource-contract coverage.
The resource-request queue gate then materializes one executable request row
per selected resource, which lets evaluations count whether each primitive
action has concrete local/frontier literature, formal-library, proof-feedback,
route-revision, or cross-prover dispatch packets with declared contract fields
and acceptance gates. The request rows use the selected resource's own
contract id and request/response fields, so frontier literature tools are not
audited with prover-feedback fields and prover-feedback adapters are not
audited with literature-response fields. Publication-bundle audits recheck this
cross-artifact alignment by resolving every request row back to the bundled
action-resource row and comparing the selected resource's contract map. They
also validate the row and nested-payload `dispatch_spec`, so stale command,
MCP/CLI hint, expected artifact, or adapter-surface data cannot silently pass
as a reusable request packet.
The resource-response ledger gate then materializes the other side of that
interface, so evaluations can count responses present, awaiting, contract-valid,
route-revising, or rejected without treating adapter feedback as theorem proof.
Publication-bundle audits also resolve every ledger row back to the bundled
request row and check that matched plus missing response fields exactly cover
the request's resource-specific response contract. When route-revision overlay
artifacts are bundled with the ledger, audits also verify that
`resource_response_ledger:*` overlay evidence ids resolve only to accepted,
response-present, contract-valid ledger rows and that
`applied_resource_response_traces` match those ledger rows, including compact
dispatch and minimal-delta readiness context, without carrying the full response
payload. Overlay rows also
expose compact awaiting/rejected resource-response status counts for the
route-stability audit; bundle audits recompute those summaries and
awaiting/rejected request-id lists from the bundled ledger rows before
accepting them as reusable planning signals. Bundled stability rows are also
checked against those overlay request-id lists, and interactive-session rows
carry the same ids into their next-command guidance. Bundle audits compare
interactive rows back to stability rows so stale UI/orchestration state cannot
hide awaiting or rejected resource-response work. Feedback LLM route-planner
request packets also publish interactive route-adoption-precondition
target-primitive counts, keeping scoped repair obligations visible through
prompt staging, model-tier selection, and public bundle audits. The integrated
`research-system-audit` republishes these bundle-audit counters, including
resource request payload/dispatch checks, route-revision traces,
route-stability status consistency, and interactive-session status consistency,
so AI Statistician release runs expose the same reusable-component invariants.
They are not proof evidence.
The adapter registry similarly publishes a row JSON Schema for the frontier
tool/MCP inventory so external deployments can validate readiness metadata and
response-contract fields before wiring live tools into the route-revision loop.
The prover-adapter contract similarly publishes a packet JSON Schema for
incoming target-prover work items, alongside response and response-validation
row schemas, so external Rocq/Isabelle/Agda adapters can validate both sides of
the mapping interface before any kernel replay claim is considered.
The portable plan and publication bundle also publish the route-alignment edge
JSON Schema, validating the source informal-DAG node, formal realization
candidate, primitive, action class, alignment status, and proof-boundary fields
that target-prover packets preserve.
They also publish the minimal-delta decision-row JSON Schema, validating the
per-route costed cut and structural minimality proxy separately from theorem
proof evidence.
The benchmark route-row and evaluation-row JSON Schemas validate route-truth
labels and row-level diagnostic scores separately from theorem proof evidence.
The cross-prover matrix audit aggregates that same packet-schema validity
across Lean4, Rocq, Isabelle, and Agda exports; it also publishes matrix-row
and response-validation-row validity counts. Publication-bundle audits fail
copied matrix artifacts if any target-family packet, matrix row, or
response-validation row is schema-invalid.

`formal-verifier-queue` is the handoff from that diagnostic to theorem work:
it records whether hard-mode dependency-graph RAG increased the candidate
frontier, whether related subclaims have verifier/search history, and whether
the route has plausible source and semantic support, but keeps those signals
separate from proof status. A queue row is still unproved until AXLE/local Lean
accepts the referenced theorem or bridge proof. `formal-verifier-replay-export`
is the next handoff: it converts those planning signals into route-level replay
tasks and replay-policy examples, including kernel-calibrated and
proof-search-solved subclaim replay where available. Those replay tasks are not
theorem proof evidence; they are the contract for the next full theorem or
bridge proof attempt. `formal-verifier-replay-attempts` now performs those
attempts when requested, using placeholder-stripped formal-gap skeletons.
`formal-verifier-replay-calibration` then records whether those attempts are
still missing, failed with repair feedback, accepted only by a non-kernel
verifier, or accepted by AXLE/local Lean. The next prover milestone is to repair
the highest-priority failed theorem/bridge routes and increase the
`full_route_kernel_verified` count.

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

Recent formal-verifier improvement: patch-rerun residual obligations now export
worker-ready prompt packets with patched artifact context, rerun commands, and
output contracts. This makes exact proof-bank reuse, bridge-chain composition,
and source-discovery blockers actionable without weakening the proof-evidence
boundary. A residual-response validation gate now audits worker outputs from
those packets, treating missing responses as awaiting work and rejecting any
proof claim that lacks full patch-rerun kernel calibration.
The deterministic residual autoworker now fills that response channel with
non-proof patch proposals or retrieval queries so the system can validate
response contracts before asking for stronger Lean evidence.
A residual follow-up queue now routes those validated non-proof responses into
ready patch-rerun or source-discovery work items, preserving the same
full-route kernel-calibration boundary.
