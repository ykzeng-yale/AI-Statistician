# Publication Programme

Updated: 2026-10-04. Status: design and release work in progress; no new scientific
benchmark result. The native chat goal is active and covers both publications.

## Execution Roadmap

The checklist below is the single source of completion status. This map connects
its items to concrete paper deliverables; it is not another checklist, scheduler
or requirement to invent a new statistical theorem. Each result must distinguish
what the research agents delivered from operator preparation and assessment.

| Work package | Items | Required deliverable | Paper placement and completion evidence |
| --- | --- | --- | --- |
| Scientific contribution and qualification | Q01--Q07 | Distinct H/S questions; exact task/access roster; executable reference scope; independent assessment protocol; actual arm conditions; prospective code/model/resource/schedule freeze | Both Sections 1--4 and A01/A03. A dated, hash-bound protocol precedes official calls; candidate configurations and mock tests alone do not complete this package. |
| Theory and agreement | T01--T05 | Reviewed evaluation mathematics plus complete selected agent-authored Markdown/LaTeX case arguments, claim-level assessment, and theory/code/data/report correspondence | Both theory appendices and the essential claims in Section 5. Full definitions, assumptions, derivations and invoked-result conditions are supplied; a missing or rejected argument remains visible. |
| Harness comparison | E02, E05--E06 | All scheduled within-host bare/package draws; actual uptake; exact final-artifact adjudication; prespecified contrasts and complete cost/failure accounting | H main outcome table and resource figure, W02, A03/A06. Cross-host compatibility is reported separately, not pooled as efficacy. |
| Collaboration comparison | E03, E05--E06 | All scheduled free-planning, shared-workflow, no-reverse-revision and full-collaboration draws under the frozen conditions; common external adjudication and bundle-specific contrasts | S main four-arm outcome table and resource/behavior figure, W03, A03/A06. Role names or internal acceptance do not establish collaboration benefit. |
| Statistical-method simulations | E01, E04 | Per-task ADEMP design; frozen method/source and comparators; fresh datasets; every replication and failure; estimand-aligned summaries and Monte Carlo uncertainty | Main scientific summaries and A04/A06. Inner datasets are not additional agent draws; finite simulation does not prove a theorem. |
| Substantive application | Q03--Q04, C01--C05 | Declared complete B1 reconstruction and Card E.1 analyses, exact aggregation, uncertainty, assumptions/sensitivity, assessed theory and traceable agent behavior | Both Section 5 drafts completed under W04, with full A02/A04 material. Missing TSCI helper/data/aggregation cannot be replaced silently; this case dependency does not halt otherwise qualified primary comparisons. |
| Optional formal foundation | T06, A05 | Compact curated Lean API and source/dependency/axiom evidence for precisely the formal claims actually made | Scoped optional-Lean appendix. No whole-textbook, autonomous-proving or general prover-performance claim from library compilation. Non-formal experiments do not wait for this package. |
| Manuscripts, release and submission | W01--W05, A01--A06, R01--R05 | Evidence-backed H/S main texts; complete mathematical, protocol, simulation and reproduction supplements; rights; clean installation; independent full-paper review; checked submission packages | The two existing manuscript masters and common supplement remain authoritative. Results determine the abstract/discussion; missing outcomes are not filled with expected success or synthetic numbers. |

**Current position:** Q01/T01/C01/W01 are limited scope or draft deliverables.
Official H/S comparisons, full assessed case arguments, confirmatory simulations,
results sections and release rights are not complete. No publication readiness
percentage is computed from this map.

**Next executable deliverable:** finish the selected tasks' access/reference and
numerical endpoint qualification, resolve independent assessment, and freeze one
study package. Then execute its entire scheduled comparison and adjudication,
instead of alternating indefinitely between new task panels, architecture changes
and unselected numerical checks. Preserve unsuccessful draws; a negative effect
is reportable without redefining success.

The minimum scientific scope is a justified comparison of the implemented
intervention on the declared roster/model, not universal research automation.
The standard evaluation calculations in T01/T05 are not a novelty claim. The
case's substantive mathematics must be independently assessed whether it invokes
published theory, derives a conditional result or fails to establish a claim.
Cross-model generalization, human time savings, frontier discovery, new statistical
theory, independent parallel execution, learned policies and complete textbook
formalization require their own evidence and are deferred unless explicitly made
part of a prospectively qualified claim. Do not turn them into mandatory side
projects for these two papers.

## Two Research Questions

**Paper H: A Portable Harness for Reviewable Statistical Research.** Can a small,
host-independent research guidance package improve the
correctness and reproducibility of statisticians' existing coding
agents? Researchers keep their host agent and model. Theory lives in
Markdown/LaTeX; computation uses local Python/R; Lean is selected by task intent.
The deliverable is an installable skill/tool package, reference workspaces and
reproducible host conformance, followed by scientific comparison. A human-effort
study is optional and required only for a separate researcher time-saving claim.
Installing a skill alone does not establish either improvement or novelty.

**Paper S: AI-Statistician, a Single-API Collaborative Statistical Research
System.** Does scoped specialist collaboration improve externally verified
statistical research outcomes over a single source-owning agent at comparable resources?
The system supplies its own retained model/tool sessions and sole outer graph;
it does not invoke Codex or Claude Code to do the research. Separate theory,
scientific-code, simulation and referee sessions use the same base model API.
The research contribution must concern effective collaboration and evidence,
not merely a diagram with more named agents.

Both papers disclose the shared implementation and cite each other. Paper H
tests the portable layer added to a host; Paper S tests collaboration within
the independent system. Do not publish the same experiment twice as independent
evidence or claim two novel architectures from one renamed implementation.

`EmpericalProcessLEAN` supplies a reusable, source-mapped Lean foundation for
both papers. It is not automatically a third publication or evidence of complete
textbook formalization. A separate library paper would require its own curated
mathematical contribution and evaluated coverage.

## Statistical Research Contract

Methods research begins with a precise inferential question, estimand, model,
assumptions and comparison, not a paper-writing template. Distinguish
identification, estimation, computation and inference. A reviewable theoretical
claim has definitions, a stated scope, equation-level justification, necessary
conditions and unresolved gaps. A valid derivation can disprove the proposed
claim or establish a conditional result.

Theory and exploratory code can inform each other. Replicate a relevant pinned
baseline when sources permit, then investigate extensions. Stable claims receive
independent mathematical and implementation scrutiny. Confirmation uses frozen
DGPs, estimands, competing methods, performance measures and uncertainty rules.
Simulation assesses specified scenarios, not universal theorem correctness.
The ADEMP/Monte Carlo reporting standard is the scientific reference, not a
mandatory agent action sequence. [Morris, White and Crowther](https://doi.org/10.1002/sim.8086).

Lean can inspect definitions or stable lemmas early, and perform deep proof after
statement stabilization. It blocks only explicitly formal tasks. Kernel closure
certifies the encoded statement; source fidelity also needs semantic review.
Open research remains exploratory until externally scrutinized; model agreement
does not establish novelty or mathematical truth.

## Architecture Decisions

| Layer | Reuse now | Missing release requirement |
| --- | --- | --- |
| Portable host | Native host file/edit/search/execution tools and Agent Skills format | Clean installation, actual body activation, reference/tool access and a substantive reproducible use case |
| Retained research session | `client_tool_loop.py`, hash-bound files and raw observations | Local Qwen conformance for every workspace and long-session recovery |
| Collaboration | `agent_runtime.py`, scoped roles and reference handoffs | Dependency-aware independent work, exact-input joins and evidence invalidation; current execution is serial/interleaved |
| Scientific execution | Existing local Python/R projects; native Python/R share the pinned local executor | Actual matched study access, environment reconstruction and clean-machine reproduction |
| Verification | Independent review, frozen confirmation and exact Lean checks | Qualified independent Qwen-era evaluation plus expert calibration |
| Lean foundation | Pinned Mathlib/Statlib/StatInference and retrieval | Audited statement/proof/dependency maps and a compact curated public API |

Extend the sole runtime if independent scheduling is justified; do not layer a
second framework over it. Model authors all derivations and code revisions. The
harness supplies tool state, execution, source identity, permissions and evidence
authority. Do not add theorem-family logic, grammar repairs or generated-answer
patches. A demonstration of a model error is not by itself a harness defect.

## Current Audit Evidence

The initial audit inspected AI-Statistician `4c0a1ade` and EmpericalProcessLEAN
`4cec7860c`. Both were clean and their remotes were fetched. It inspected canonical
entry points, session/provider contracts, installation metadata, source maps,
Lean tooling and branch ancestry; it is not a claim that every source line or
external paper has received expert review.
The [integration follow-up](publication_lean_integration_20261002.md) records the
subsequent pinned source, selected checks, PR comparison and release-access boundary.

- The full `StatInference` root built locally on Lean 4.30.0 (9843 Lake jobs,
  including cached replay). This is not a clean-machine or all-declaration axiom
  audit; the root file has zero declarations to scan.
- The separate [fresh-source check](../benchmarks/publication_foundation_rebuild_20261003/README.md)
  timed out before root completion under its recorded environment and 3600-second
  budget. No local-library build artifacts were reused; third-party caches were.
  It is not a passing reconstruction, a proof rejection or a new agent outcome.
- The library has 1361 Lean files. Its 611 source-map rows cover 173 distinct
  `(book, source_kind, source_label)` items: 509 foundation, 73 proved-general and
  29 proved-exact rows. These are existing author labels, not independently
  established theorem coverage. Some items have multiple mappings.
- 50 remote Lean refs were inspected: 37 are ancestors of main, 13 are not.
  An unmerged ref may be superseded or duplicated; ancestry alone does not justify
  a merge. Review mathematical deltas and source statements before integration.
- Both repositories lack a top-level license. Source-textbook redistribution and
  third-party attribution need a rights inventory before an installable public
  release. Do not assume the owner's request establishes third-party rights.
  Anonymous Lean repository-page/API access returned 404 on 2026-10-03; configured
  operator Git access does not establish public release availability.
- Existing strict development closure is still 0/2. Historical scoped credits,
  unit tests and transport checks do not create a new full-system success rate.
- The default backend is local Qwen. Forward runtime model bindings and semantic
  protocols 26/27 separate new local evaluation from historical Haiku authority.
  Scientific qualification is still pending; no old evaluation or qualification
  is rerun, relabelled or rescored.

### Historical Evidence Boundary

The Haiku development runs are not defensible comparative publication experiments:
the harness, tasks, review contracts and settings changed during debugging; the
recorded credits have different scopes, and the revealed tasks are not a fresh
test sample. Keep their original artifacts as an archive, not an active scorecard,
main result table or baseline. Do not spend further calls following those results.
Formal experiments for both papers start prospectively with open-weight models.

The preserved [trimmed-mean audit](operator_audits/trimmed_mean_l0_v1.md)
records internal acceptance but independent full-task rejection; the
[betareg audit](operator_audits/betareg_gasoline_precision_l1_v1.md) records
automated acceptance that missed an explicit task restriction. These are useful
failure analyses, not validated successes or a controlled estimate of efficacy.
The archived seven mixed-scope credits must not become a research-E2E numerator.

Retain useful implementation and regression tests. An existing independently
checked Lean theorem may support the curated library irrespective of its authoring
model, after source-fidelity and rights review. That artifact is a library result,
not evidence that the agent autonomously completed a research task. Historical
failure traces may support a labelled development narrative, not an efficacy claim.

## Comparative Experiments

The publication experiment specification is in
[publication_experiments.md](publication_experiments.md). It is a design proposal,
not an activated or retrospectively registered experiment. Exact paper tasks,
independent gold, budgets, repetitions and analysis must be frozen before calls.

Paper H compares each host with and without the identical portable package.
Host/model differences are recorded rather than attributed to the harness.
Cross-host installation is a conformance result, not scientific accuracy. Official
scientific experiments use open-weight models. The operator also authorizes the
installed local Claude Code host for portable compatibility/user-workflow tests,
reported separately; direct Anthropic API experiments remain excluded.

Paper S compares a free-planning general agent with identical tools, a
single-context same-workflow control, role-separated agents without reverse
author revision, and the complete collaborative system. This operational ablation
retains forward review and local tool feedback; its precise scope and attribution
limits are in the experiment specification. The single-context arm exposes
shared history and does not receive independent-review credit for self-review.
Use the same Qwen weights, endpoint, task access and global resource envelopes.
An additional minimal external research harness can be run where its backend and
license permit; report adaptations. Published scores from different models/tasks
are related work, not comparable baseline measurements.

Lean component comparisons separate proof of an exact supplied Lean statement,
natural-language formalization and source-fidelity review. Test zero-shot,
compile-feedback and feedback-plus-retrieval with equal target information.
Library reuse is a separate intervention; exclude target proofs and dependent
aliases from retrieval. Compare against accessible ReProver/minimal-agent
implementations only after environment and model compatibility are established.

## Delivery Checklist

The first methods drafts are [portable harness](../manuscripts/portable_harness.md)
and [collaborative system](../manuscripts/collaborative_system.md). They distinguish
implemented mechanisms from proposed studies and report no comparative efficacy
or usability result. They are not submission-ready manuscripts; qualified fresh
scientific tasks, common external authority, matched conditions and release rights
remain unfinished. Historical Haiku results are not inserted as result tables.

The [isolated foundation check](../benchmarks/publication_foundation_migration_20261002/README.md)
failed the full library build against the proposed Lean 4.33.1 dependencies.
The active Lean/RAG pin is unchanged. Compatibility failure does not invalidate
the old compiled foundation or block optional-Lean research tasks.

This is the single paper-delivery checklist, not a runtime controller or a new
capability scorecard. An unchecked item remains incomplete even when a draft or
test exists. Checked items name their limited deliverable, not publication
readiness. Update items when their evidence changes; do not count them into a
readiness percentage. Work through the dependencies below without reopening broad
literature inventories, unrelated numerical panels or infrastructure campaigns.

### 1. Scientific Scope and Study Qualification

- [x] **Q01. Distinct questions and attribution.** Paper H tests package uptake
  within the same coding host; Paper S tests the standalone collaboration bundle.
  The masters and this programme state the contrasts, overlap and limitations.
- [ ] **Q02. Qualified multi-family roster and split.** For each primary task:
  record the paper/edition, inferential domain, access condition, exact deliverable,
  theoretical and computational obligations, reason for inclusion, reference and
  rights. Keep families together; exclude exposed development families from the
  official test pool. Freeze weights and counts with a precision rationale, not
  an arbitrary large task count. Current roster remains unfrozen.
- [ ] **Q03. Complete case inputs and source reconstruction.** Preserve the
  [TSCI B1/Card candidate](../benchmarks/publication_case_candidates/tsci_b1_card/README.md),
  paper/code/data identities and original sources. Available 76-file capsule is
  prepared; missing `Source-otherRF-hetero.R`, original data rights and clean
  reconstruction are unresolved. No silent replacement or operator implementation.
- [ ] **Q04. Qualified executable references.** Execute the exact intended
  producer/aggregation and application scopes, record discrepancies and failure
  behavior, and fix numerical tolerances before draws. Existing package examples
  and environment probes do not qualify B1/E.1 or a full-paper endpoint.
  The [selected-source result follow-up](../benchmarks/publication_case_candidates/published_methods/source_final_projection.json)
  closes a prospective assessment-input gap: the common evaluator now receives
  complete selected result/stream bytes for runtime/shared controls, not only
  manifests and summaries. Exact files and missing results are preserved without
  selecting a better attempt. Opaque fixture grading is not numerical or
  mathematical qualification. The assessment draft now separates deterministic,
  literal-reconstruction, stochastic and discrepancy endpoints; no task-specific
  complete endpoint/coordinate map, tolerance, precision or authority is frozen,
  so Q04 remains open.
  The [native R assessment follow-up](../benchmarks/publication_case_candidates/published_methods/r_artifact_assessment.json)
  removes the Python-only artifact restriction using the same executor and ABI.
  The assessment-only R reader now preserves the three declared R result
  channels' keys, slots and nonfinite states; fresh native/CLI fixtures pass.
  Source-defined endpoint quantities are explicit in the assessment draft.
  This is not author-result comparison, scope completeness, tolerance qualification
  or a scientific verdict; no further item is checked.
  The [StepMix printed-channel reader](../benchmarks/publication_case_candidates/published_methods/read_stepmix_tables.py)
  now preserves simulation/GSS/package-comparison coordinates, original lines,
  printed precision and explicit missing sections. Fresh fixtures exercise actual
  pandas 1.5.3 rendering and malformed inputs without reading old author outcomes.
  It supplies no complete-stage/grid verdict, numerical accuracy/tolerance or
  theoretical assessment; Q04 remains open.
  The assessment draft now states complete literal source-stage/grid coordinates,
  raw/display-label maps, timing multiplicities and distinct application/simulation
  model conventions for the three primary candidates. These definitions precede
  any draw, but do not qualify accuracy, alternatives, authority or confirmation.
  Opaque RDS/native-dispatch and negative checks pass; typed missing/nonfinite
  values remain in the captured object. These are mechanism checks, not author
  RDS/RData assessment or scientific endpoint qualification. The protocol now
  distinguishes each source-format channel, coordinate map and missingness;
  Q04 is not closed.
- [ ] **Q05. Independent mathematical authority.** Freeze claim rubrics, valid
  alternative arguments, negative/underspecified controls, assessor qualifications,
  conflicts, blinding and adjudication. Obtain assessor appointments; none is
  currently established. Missing authority cannot be replaced by Qwen voting.
  The [public-obligation assessment draft](../benchmarks/publication_case_candidates/published_methods/assessment_protocol.md)
  now specifies exact-final review scope and unresolved decisions without giving
  agents mathematical answers or numerical gold. It does not close Q05/A01.
- [ ] **Q06. Comparable actual conditions.** Verify tool/source/data access,
  execution profiles, effective model requests, revision opportunities, confirmation
  exposure and resources across H's two arms and S's four. Record irreducible
  differences; equal calls or arm names are not qualification.
  The [candidate request follow-up](../benchmarks/publication_case_candidates/tsci_b1_card/arm_request_alignment.json)
  aligns required-tool policy and binds the complete shared request. The observed
  initial Architect transport and differing batch policies remain explicit; opaque
  fixtures are not live full-arm qualification, so Q06 stays open.
  The historical [arm assembly](../benchmarks/publication_case_candidates/published_methods/arm_conditions_preparation.json)
  binds the original unactivated proposal at its code pin. The
  [current follow-up](../benchmarks/publication_case_candidates/published_methods/prospective_conditions_followup.json)
  rejects unsupported active scoring dimensions before calls, preserves scientific
  instructions and binds twelve corrected S configurations plus six paired H
  workspaces. Native host mock checks establish body activation/output settings,
  not research or matched access. Final-tree collection uses the existing reader;
  the [native final-view follow-up](../benchmarks/publication_case_candidates/published_methods/native_final_projection.json)
  now preserves exact multi-file Python/R projects and binary result files through
  the common evaluator. Opaque execution fixtures verify dispatch and distinct
  source/result failures, not scientific interpretation or acceptance. Six new
  paired H workspaces bind the explicit entrypoint contract; earlier unactivated
  preparation is unchanged. The subsequent
  [native access observation](../benchmarks/publication_case_candidates/published_methods/native_access_observation.json)
  uses six disposable copies and scripted responses, with no model inference or
  author-study execution. Both H arms expose the planned text/source reads, real
  CSV/RDA parsing and opaque Python/R failure/edit/rerun feedback. All 482 registered
  source copies remain exact. Initial fixture-client approval cancellations are
  retained. `Read` rejects PDFs; paired text is readable, not fidelity-qualified.
  Manual per-call ACP approval and unrestricted native shell are not equivalent
  to S's sandbox authority. Complete effective permissions, PDF fidelity, long
  sessions, matched opportunities, qualified numerical endpoints, independent
  authority and freeze remain open.
  Q06 is not complete.
- [ ] **Q07. Prospective freeze.** Bind exact code/package, local Qwen weights,
  quantization/runtime/template/decoding/hardware, task and authority versions,
  schedule/RNG/order, stopping, all outcomes and analysis. Confirm the chosen
  deployment is available. Freeze before the first official call; no study is
  currently activated.
  The [deployment prerequisite](../benchmarks/publication_deployment_qualification_20261003/README.md)
  recovered the identical missing weights and observed one proposed startup and
  short synthetic tool turn. Its explicit API limitation, untested long-session
  behavior and still-unfrozen study conditions keep Q07 open; it is not an official
  scientific draw and does not change consumed records.

#### Roster Qualification Evidence

This table is the current candidate decision, not a frozen task list. A paper
with runnable code is not automatically eligible for an integrated-theory endpoint.
The actual question/access condition determines exposure and scientific scope;
changing a version never rehabilitates a consumed problem family. Background
overlap is recorded rather than treating every application of a shared statistical
principle as an independent test or excluding all of statistics.

| Candidate domain | Existing reference scope | Decision before Q02/Q04 can close |
| --- | --- | --- |
| TSCI invalid instruments | Separate JSS package example is numerically qualified; final JMLR B1/Card source inputs are prepared | Retain the substantive case. Missing B1 comparator helper, Card Table 15 aggregation/seed specification, exact case reference and independent theory assessment remain unresolved. |
| Zero-inflated copula count regression, bizicount | Full unchanged main script executed, including 4,000 simulation slots | Discrepant standard errors, missing fits, optimizer codes and the source BIC convention prevent automatic use as scientific truth. Qualify a stated literal-reproduction or discrepancy-detection endpoint and rights separately. |
| Empirical-Bayes normal means, ebnm | Unchanged default main-text run and exact finite numerical agreement within its inspected scope | Numerical-only reference exists; full timing/licensed appendix and independent theory do not. Existing James-Stein/Tweedie development exposure prevents calling a generic normal-means rederivation untouched. Exact source-task grouping still needs an explicit decision. |
| Latent-class/profile models with external variables, StepMix | All six planned unchanged Python invocations finished, including the three full grids and GSS; Table 3 differs, selected other tables agree at displayed precision | Preserve emitted/suppressed convergence warnings, deleted extreme fits and absent per-repetition exports as limits. Existing Gaussian-mixture EM exposure excludes a generic EM rediscovery claim. Any distinct misclassification-correction task, rights, reference acceptance and split must still be qualified. |
| RepliSims propensity-score matching, meta-analysis, ordinal factor analysis and mediation | Partial probes or discovery only; some source identities/rights unresolved | Do not present a human reimplementation as original author code or a narrow successful probe as a full reference. These are deferred, not selected primary tasks. |

The [earlier qualification record](../benchmarks/publication_reference_qualification_20261002/README.md)
and [new StepMix record](../benchmarks/publication_reference_qualification_20261003/README.md)
bind these limits. DoubleML, CORE Type-M/Type-S, scikit-fda and fixed-K L2
segmentation remain excluded from the fresh test pool because their development
draws were consumed. None of the rows above is a new model result, official draw,
independent mathematical acceptance or a reason to mark Q02/Q04 complete.

The [exact-task selection follow-up](../benchmarks/publication_case_candidates/published_methods/README.md)
now supplies three loader-readable integrated candidates for StepMix external
variables, ebnm prior-family comparison and bizicount reconstruction/assessment.
All use declared paper/code access, not blind rediscovery. Background EM and
normal-means exposure remains explicit; TSCI stays an exposed case/illustration.
The source records support only their qualified numerical scope. The
[input preparation](../benchmarks/publication_case_candidates/published_methods/input_preparation.json)
now supplies three existing-format model-visible snapshots with exact original
assets and cached-output exclusions. All 225 selected author files are byte-identical;
the three PDF/text pairs make 231 registered files. The bizicount text extraction
has an explicit rotated-text omission warning; full PDFs remain available, but
text fidelity and actual host PDF access are unqualified. Eight existing source/import
tests passed without a model call or scientific script. Execution bindings, task
ABIs, rights, independent assessment, actual arms and roster/precision freeze remain
required. This prerequisite does not close Q02/Q04 or activate a study.
The [candidate execution bindings](../benchmarks/publication_case_candidates/published_methods/execution_preparation.json)
now connect the unchanged input documents to pinned local interpreters and adapted
libraries. Configuration loading is not full execution: a synthetic native R
two-worker fixture failed to open its local server socket, and StepMix's generated
Python environment is not the native author environment. Resolve these shared
execution/access gaps before Q06/Q07; do not add another candidate or substitute
serial toy computation for the declared study. No author script or model ran.
The [native-resource follow-up](../benchmarks/publication_execution_resources_20261003/README.md)
adds an explicit shared local-port capability; synthetic FORK/PSOCK workers now
execute. Its inbound-listener limitation is disclosed. This does not change the
earlier failure, configure the candidate studies, establish multi-agent concurrency
or close Q06/Q07. Native Python and actual matched scientific access remain open.

The subsequent [shared native scientific check](../benchmarks/publication_case_candidates/published_methods/native_scientific_execution.json)
qualifies native Python/R configuration and ABI mechanisms at b2569e26: 47 configured
checks and the full default regression pass. Existing StepMix package construction,
project/estimator/input binding and Theory scratch execute; all 6,611 environment
entries remain exact. This is not an author-method run, model study, independent
theory assessment or matched-arm qualification. Scientific checklist items stay open.

### 2. Theory and Scientific Agreement

- [x] **T01. Evaluation-method appendix draft.** The shared
  [supplementary methods](../manuscripts/supplementary_methods.md) states the
  benchmark estimand, expectation calculation, conditional interval assumptions
  and simulation estimands. These are standard evaluation methods, not a new
  statistics theorem, an agent result or independently certified mathematics.
- [ ] **T02. System-produced case argument.** Obtain selected Markdown/LaTeX
  definitions, estimand, assumptions, identification argument, estimator/inference
  explanation and equation-level derivations from the actual research agents.
  Distinguish invoked published results from independently derived claims;
  preserve conditional conclusions, counterexamples and unresolved dependencies.
  The [consumed TSCI preparation](../benchmarks/publication_case_candidates/tsci_b1_card/theory_preparation_results.json)
  read sources and wrote one unselected file, but rejected handoff writes ended
  the session without a checkpoint. No argument is selected or independently
  assessed; T02 stays open. Do not salvage the partial file or rerun this result.
- [ ] **T03. Independent argument assessment.** Assess every substantive claim
  and its exact selected argument under Q05. Localize unsupported steps, changes
  in assumptions, normalization and rate errors; retain disagreements and unresolved
  claims. No complete gold-covered scientific task has been established.
- [ ] **T04. Theory/code/report agreement.** Bind each assessed estimand and
  method to actual source and data, variance/selection conventions, experiment
  output and interpretation. Reject a correct number attached to a different claim.
- [ ] **T05. Review the paper's evaluation mathematics.** Independently check
  T01 against the final design, including independence, missing assessment,
  weighting and uncertainty. Do not apply a bound merely because it is written.
- [ ] **T06. Scoped optional Lean evidence.** For any formal claim made in either
  paper, provide source correspondence, active imports/pins, kernel/axiom evidence
  and human/agent attribution. Qualify zero-shot, compile-feedback and scoped-RAG
  comparisons only if prover performance is claimed. No non-formal task must wait
  for textbook coverage, a migration or a new proving benchmark.
  A [candidate nine-theorem/eight-module import scope](publication_lean_integration_20261002.md#candidate-import-scope-for-the-shared-appendix-2026-10-04)
  now distinguishes Statlib consumers, GC convergence modes and exact bracketing
  and barrier assumptions. Five newly selected existing declarations passed a
  current guarded module/axiom check; five others retain their unchanged earlier
  kernel-only evidence. This advances A05 preparation, not source fidelity,
  whole-library API certification, clean reconstruction or agent performance.

### 3. Experiments and Simulation

- [ ] **E01. Frozen simulation designs.** For each method task specify aims,
  DGP/scenarios, estimands, comparators, information access, performance measures,
  RNG/streams, failures and Monte Carlo precision. Separate literal replication
  from a justified extension. No universal 100-repetition or nominal-coverage gate.
- [ ] **E02. Fresh Paper H comparison.** Run every scheduled bare/package draw
  under Q07; verify actual body uptake and retain uptake failures, absent finals,
  costs and interventions. Compatibility observations are not these outcomes.
- [ ] **E03. Fresh Paper S comparison.** Run free planning, shared workflow,
  no-reverse-revision and full collaboration on integrated tasks. Retain all
  stopping causes. Source-only tasks cannot identify collaboration effects.
- [ ] **E04. Confirmatory method execution.** Execute frozen exact source on
  the specified fresh cohorts, retaining per-repetition results and failures.
  Check MCSE and the declared stopping rule; do not alter metrics after outcomes.
- [ ] **E05. Common final-artifact adjudication.** Evaluate the exact final
  selections in all arms, including missing/unresolved material, with the same
  qualified independent authority. Do not salvage intermediates, retry consumed
  failures or rescore old Haiku/Qwen development draws.
- [ ] **E06. Complete comparative analysis.** Produce family-by-arm counts,
  prespecified paired contrasts and justified uncertainty, component outcomes,
  failure causes and complete time/token/computation accounting. Distinguish
  outer agent draws from inner datasets and purposive-roster results from
  task-population claims. Release negative results; no official effect exists yet.

### 4. Substantive Case Study

- [x] **C01. Bounded case candidate.** The public question distinguishes B1's
  seven methods and Card Appendix E.1's four basis analyses, oracle access,
  theory/code/empirical intent and non-required Lean. It is a candidate, not a
  selected passing case or an untouched held-out family.
- [ ] **C02. Complete published B1 reconstruction.** Resolve Q03/Q04; account
  for all 18 declared settings and 25 rounds per setting, the seven requested
  methods, aggregation, uncertainty and unavailable/failed fits. One batch or
  software example cannot stand for the full design.
- [ ] **C03. Card E.1 application.** Execute all four specified basis analyses
  with exact data, covariates, splits and aggregation. Explain the wage/schooling
  estimand, instrument, comparison and assumption sensitivity. Do not relabel
  E.1 as main Figure 4 or infer instrument validity from numerical agreement.
  The inspected pin supplies the producer but no reader for its named output;
  Table 15's exact aggregation and original RNG specification remain unresolved.
  Original seeds are needed for exact historical replay, not for every stochastic
  reproduction; qualify a declared new schedule separately without filling the
  missing aggregation or comparator by numerical guesswork.
- [ ] **C04. Independent scientific interpretation.** Connect T02--T04 and
  C02--C03; separate reproduction, adaptation, reimplementation and new theory.
  Clearly bound causal and asymptotic claims. Preserve the published proof/source
  discrepancies until independently resolved, without operator proof repair.
- [ ] **C05. Case selection and behavioral account.** Predeclare the case's role
  in each paper. H reports the host intervention; S traces meaningful specialist
  findings and same-owner revisions against external outcomes. Show failures and
  human interventions, not just a successful vignette. Shared case material is
  disclosed once, never counted as two independent efficacy results.

### 5. Main Papers and Appendices

The two Markdown files remain the manuscript masters. Use the common supplement
for shared methods; per-task arguments and results remain separately attributed.
The [placement map](../manuscripts/supplementary_methods.md#s8-manuscript-placement-and-result-material)
names the required tables, figures and supplements without inventing their values.

- [x] **W01. Methods masters.** H Sections 1--4 and S Sections 1--4 have draft
  questions, closest-work discussion, implemented interventions, evaluation and
  analysis. Native R scope and shared appendix are now aligned. This is drafting,
  not independent review or a measured efficacy claim.
- [ ] **W02. Paper H results.** Write qualified installation scope separately
  from E02/E05/E06 scientific contrasts, with uncertainty, uptake, failures,
  resource use and operator interventions. No time-saving claim without its own
  researcher study.
- [ ] **W03. Paper S results.** Write E03/E05/E06 with all four arms, exact
  contrast interpretations and internal/external verdict disagreement. Do not
  attribute a bundled difference solely to memory, review quality or parallelism.
- [ ] **W04. Case sections.** Complete each paper's Section 5 from C02--C05,
  with essential scientific results in the main text and full materials below.
- [ ] **W05. Discussion, title and abstract.** Revise only after results;
  address source/model/roster scope, contamination, grading authority, dependence,
  negative findings, software limits and overlap. Remove unsupported superiority,
  autonomous-discovery, theory or entire-textbook claims.
- [ ] **A01. Task and assessment supplement.** Supply the roster, edition/access
  mapping, split/exclusions, rubrics, reference qualification and assessor record.
  Keep held gold out of author tools until assessment; release it afterward where
  permitted, without exposing unused sealed tasks.
- [ ] **A02. Complete mathematical supplement.** Include every assessed selected
  case argument, definitions, assumptions, dependencies, full calculations and
  localized assessments from T02--T04, plus independently reviewed T01/T05.
  No equation snippets or finite numeric checks in place of a proof.
- [ ] **A03. Protocol and trajectory supplement.** Release all scheduled draws,
  exact final/source/input identities, prompts/tools, pins, budgets, RNG/order,
  costs, interventions and stopping causes. Protect credentials/private reasoning;
  report unavailable records rather than fabricate them.
- [ ] **A04. Simulation and case supplement.** Release full ADEMP designs,
  methods, per-repetition outcomes, aggregation scripts, failure/MCSE calculations,
  application data/access and sensitivity analyses for E04/C02--C04.
- [ ] **A05. Lean support supplement.** Provide the compact curated inventory,
  source-statement maps, pins, dependencies, axiom checks and attribution for T06.
  Shared library checks are not two independent agent-proving results.
- [ ] **A06. Table/figure reproduction.** Connect every main/supplementary value
  to exact permitted inputs and a reproduction command. Distinguish planned from
  executed denominators, missing from zero, and mechanism from scientific evidence.

### 6. Release, Review and Submission

- [ ] **R01. Rights and attribution.** Resolve both root licenses, incorporated
  software, textbook/source text and original-data rights; establish public access.
  An author's request does not grant third-party redistribution rights.
- [ ] **R02. Clean researcher release.** Test native host activation/reference
  access and scientific Python/R workflows on a clean documented environment;
  freeze minimal installation and exact reconstruction instructions. Prepared
  operator environments and local unit tests are not clean-machine evidence.
  The [installed-tool qualification](../benchmarks/publication_release_qualification_20261003/README.md)
  now tests a committed wheel in a fresh Python environment, new HOME and separately
  prepared locked npm runtime. CLI and synthetic two-file Python/R execution/raw
  failures passed outside the source checkout, with zero model calls. This advances
  installation only; same-host binaries, macOS-only execution, untested full
  research/host workflow and unresolved rights keep R02 open.
- [ ] **R03. Independent full-paper review.** Review both complete main texts,
  appendices and scientific analyses for correctness, contribution, agreement,
  reproducibility and claim scope. Correct all consequential findings.
- [ ] **R04. Submission QA.** Supply authors/affiliations/contributions and
  acknowledgments, checked bibliography, artifact access/rights, venue-specific
  disclosure and overlap. Produce compiled, visually checked submission packages
  with no missing references, placeholders or unsupported numbers.
- [ ] **R05. Goal closure.** Verify both papers independently satisfy their
  stated contributions, reproducible comparisons and releases. Only then mark
  the native goal complete; do not infer readiness from this checklist count.

### Immediate Execution Order

For selected primary tasks, finish Q02/Q04 reference/access scope and Q05 assessor
decisions without exposing evaluation findings to authors. Qualify Q06, freeze
Q07/E01 and execute E02/E03. The exposed TSCI case's missing inputs are separate
Q03/C02/C03 dependencies: advance them in parallel, rather than hold every
otherwise qualified primary comparison for an unavailable case helper.
Adjudicate before reporting an effect; assemble T02--T04, E04 and the case into
the main texts and supplements.
Release rights and clean reconstruction can advance while assessment is pending.
Optional Lean supports scoped claims, not the non-formal study's critical path.

Experiment completion does not require every agent draw to pass or a positive
harness effect. A fully executed, independently assessed negative comparison is
reportable. Keep that distinction from accepted statistical claims, complete
case reconstruction and working releases; never change task acceptance after
observing results just to close a checklist item.

The current native scientific mechanisms and shared appendix drafting advance prerequisites
only. Missing author sources, data rights and qualified assessor appointments
remain external decisions. Until resolved, advance unblocked items of this same
programme; do not replace the case, invent authority or launch a knowingly
unqualified official comparison.

Likely venue fit is a later decision: a useful statistical software/research
workflow contribution can fit a computational-statistics/software venue; a
controlled agent architecture/benchmark contribution can fit an AI venue.
Publication in a theory journal would require substantive statistical theory,
not a software system renamed as a method. Acceptance is never assumed.

See [current sources and adoption decisions](publication_sources_20261001.md)
for dated primary papers, inspected code pins and license boundaries.
