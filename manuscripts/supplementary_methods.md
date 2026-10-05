# Supplementary Methods for the Two AI-Statistician Studies

Methods draft, 2026-10-05. Shared by Paper H and Paper S, with overlap disclosed.
No official study is activated and no result is supplied here. The calculations
below are standard evaluation and Monte Carlo methods, not new statistical
theory or proof of an agent's scientific argument. Independent review and a
prospectively fixed roster, authority and execution design remain necessary.

## S1. Units, Interventions and Evidence

A paper/problem family is the selection unit. A scheduled agent draw is one
execution of one frozen task/access condition in one arm. A simulated dataset
inside that draw is an inner repetition. Multiple rubric items, lemmas, tool
calls or datasets do not create additional paper families or agent draws.

Paper H compares the same open-weight coding host with and without the exact
portable package. Package activation and installation are measured separately;
neither demonstrates scientific efficacy. Paper S compares free planning,
shared-context workflow, role-separated work without reverse source-owner
re-entry, and full collaboration under one base-model condition. Its primary
comparison is full collaboration versus free planning. The other contrasts
have the operational interpretations in the
[experiment design](../docs/publication_experiments.md#baselines-and-interventions).
They do not separately identify review intelligence, memory or parallel speedup.

Different hosts, model weights, quantizations or resource conditions define
different comparisons unless a prospective aggregation target is declared.
Human-effort effects require a separate researcher study. Historical Haiku and
consumed Qwen development draws are not official efficacy observations.

The graph-scoped model-call meter does not equate tool or revision opportunities.
Shared component checkpoints spend ordinary actions; isolated workspace terminal
actions do not. Local action/no-progress allowances also have workspace scope.
Freeze and disclose these actual boundaries and measured computation rather than
attribute a bundle contrast to context separation or feedback alone.

Final assessment uses the selected artifacts at termination, not an intermediate
candidate, internal acceptance flag or attractive trace. The outcome records
theoretical, implementation, empirical, source-fidelity and task-intent-required
formal dimensions separately. Complete acceptance requires the frozen required
dimensions, not all available capabilities. Optional Lean remains separately
reported and does not become a completion condition for non-formal tasks.

## S2. Mathematical Assessment and Pending Authority

The independent assessor reads the selected Markdown/LaTeX argument and its exact
claim scope. The task rubric identifies definitions, assumptions, admissible
background results, necessary dependencies and acceptable alternative conclusions.
Assessment checks the substantive inferences, not a schema or textual similarity
to a published proof. An invoked theorem needs its relevant conditions checked;
an independently derived result needs its complete argument. A justified
counterexample or conditional conclusion is evaluated under the task's stated
intent rather than forced to resemble a positive reference answer.

For each claim, the assessor records the relevant source/file location, whether
the exact claim is established, an unsupported step or altered scope when
identifiable, and unresolved uncertainty. Claims about identification, estimator
construction, variance, asymptotics and empirical calibration are distinguished.
The reviewer cannot infer a proof from numerical agreement. The complete selected
argument and assessment, rather than only a theorem card, belong in the supplement.

The assessment protocol fixes qualifications, conflicts, arm blinding and
adjudication. Missing assessment is **pending**, not an adverse expert judgment
and not a score of zero silently entered into an official results table. A
completed assessment may conclude accepted, rejected or unresolved; an unresolved
required argument is not independently accepted. A final unresolved disposition
must be handled by the prospectively specified endpoint. No appointed mathematical
panel or official adjudicated outcomes currently exist.

Executable references have a separate numerical scope. They can assess faithful
reproduction under defined tolerances, not prove the source paper's theoretical
claims or observational causal assumptions. Model review is a product mechanism
or separately labelled automated diagnostic, not a substitute for missing
independent authority. Kernel proof additionally needs source-statement fidelity.

Paper access also requires source-presentation qualification. A bounded operator
comparison of six selected method pages in the three prospective journal papers
found flattened fractions, scripts and formula layout in their existing extracted
text, alongside preserved formula structures. It was not model inference, a
complete-paper audit or mathematical adjudication. The original inputs remain
unchanged; a faithful version-bound representation accessible to all compared
arms has not been qualified. Details and evidence identities are in the
[assessment protocol](../benchmarks/publication_case_candidates/published_methods/assessment_protocol.md#paper-input-fidelity-observation-2026-10-04).
The shared source reader also exposes exact original arXiv text files without
formula reconstruction. Byte-preserving access to two older author TeX archives
is verified, but localized edition differences preclude treating them as identical
journal source or independently assessed mathematics. No study capsule is replaced.

## S3. Fixed-Benchmark Target and Conditional Uncertainty

Let the qualified fixed roster contain $N$ families, one primary task/access
condition per family, positive frozen weights $w_i$ with $\sum_{i=1}^N w_i=1$,
and $R_i\geq1$ scheduled paired draws in family $i$. Equal-family weighting uses
$w_i=1/N$. If variants are included, their within-family aggregation is specified
before outcomes. Denote the roster by $\mathcal B$ and the frozen task, model,
access, execution, adjudication and scheduling conditions by $\mathcal F$.
Here $\mathcal F$ fixes the randomization law, not every realized random seed or
generated trajectory. Otherwise conditioning on a deterministic seed table and
deterministic execution can remove the repeated-run randomness being estimated.
The realized seeds are retained separately for reproduction. Any remaining
environment or assessor randomness and dependence must be explicitly identified.

For arm $a$, $Y_{ir}^a\in\{0,1\}$ denotes complete acceptance by independent
assessment in family $i$, scheduled draw $r$, after resolution under S2.
A missing final selection is not an accepted delivery. Environmental interruption,
scientific rejection, incompletion and unresolved adjudication have distinct
causes in the record. The endpoint is accepted delivered research, not an
unobserved error-free mathematical truth. Aggregate official outcomes are not
reported while required adjudications remain pending.

For arms $A$ and $B$, define the schedule-averaged target and estimator by

$$
\begin{aligned}
\Delta_{\mathcal B}^{A,B}
&=\sum_{i=1}^N\frac{w_i}{R_i}\sum_{r=1}^{R_i}
  \mathbb E[Y_{ir}^A-Y_{ir}^B\mid\mathcal F],\\
\widehat\Delta_{\mathcal B}^{A,B}
&=\sum_{i=1}^N\frac{w_i}{R_i}\sum_{r=1}^{R_i}
  (Y_{ir}^A-Y_{ir}^B).
\end{aligned}
$$

Because every summand is bounded, the expectations exist. Linearity gives

$$
\begin{aligned}
\mathbb E[\widehat\Delta_{\mathcal B}^{A,B}\mid\mathcal F]
&=\mathbb E\!\left[
  \sum_{i=1}^N\frac{w_i}{R_i}\sum_{r=1}^{R_i}
  (Y_{ir}^A-Y_{ir}^B)\mid\mathcal F\right]
  &&\text{(estimator definition)}\\
&=\sum_{i=1}^N\frac{w_i}{R_i}
  \mathbb E\!\left[\sum_{r=1}^{R_i}(Y_{ir}^A-Y_{ir}^B)
  \mid\mathcal F\right]
  &&\text{(outer linearity)}\\
&=\sum_{i=1}^N\frac{w_i}{R_i}\sum_{r=1}^{R_i}
  \mathbb E[Y_{ir}^A-Y_{ir}^B\mid\mathcal F]
  &&\text{(inner linearity)}\\
&=\Delta_{\mathcal B}^{A,B}
  &&\text{(target definition).}
\end{aligned}
$$

This expectation identity needs no independence assumption. It does not remove
grading bias, select a representative task population or establish efficacy.
Report family-by-arm counts and paired differences before the aggregate.

For the following conservative interval, assume the paired blocks
$(Y_{ir}^A,Y_{ir}^B)$ are independent across $(i,r)$ conditional on
$\mathcal F$. The two arms within a block may be dependent, and means need not
be identical. Each weighted difference lies in
$[-w_i/R_i,w_i/R_i]$. The independent bounded-sum inequality applied to both
tails, followed by a union bound, gives for $t>0$

$$
\begin{aligned}
\Pr\!\left(
 |\widehat\Delta_{\mathcal B}^{A,B}-\Delta_{\mathcal B}^{A,B}|
 \geq t\mid\mathcal F\right)
&\leq2\exp\!\left\{
 -\frac{2t^2}{\sum_{i=1}^N\sum_{r=1}^{R_i}(2w_i/R_i)^2}
 \right\}
 &&\text{(two bounded tails)}\\
&=2\exp\!\left\{
 -\frac{2t^2}{\sum_{i=1}^N\sum_{r=1}^{R_i}4w_i^2/R_i^2}
 \right\}
 &&\text{(expand the square)}\\
&=2\exp\!\left\{
 -\frac{2t^2}{\sum_{i=1}^N4w_i^2/R_i}
 \right\}
 &&\text{(sum over draws)}\\
&=2\exp\!\left\{
 -\frac{t^2}{2\sum_{i=1}^Nw_i^2/R_i}
 \right\}
 &&\text{(cancel the common factor).}
\end{aligned}
$$

This uses [Hoeffding (1963), Theorem 2, equation (2.6)](https://doi.org/10.1080/01621459.1963.10500830),
not a new theoretical result. For $K\geq1$ prespecified contrasts and
$0<\alpha<1$, a further union bound gives simultaneous coverage at least
$1-\alpha$ with radius

$$
h_\alpha=\sqrt{2\log(2K/\alpha)\sum_{i=1}^Nw_i^2/R_i}.
$$

Each interval is intersected with $[-1,1]$. Dependence across contrasts does not
invalidate this last union bound. The radius can be uninformative. A planning
requirement $h_\alpha\leq\varepsilon$, for $\varepsilon>0$, is equivalent to

$$
\sum_{i=1}^N w_i^2/R_i\leq
\frac{\varepsilon^2}{2\log(2K/\alpha)}.
$$

This is precision planning under the stated assumptions, not power evidence or
permission to add draws after seeing outcomes. No official weights, counts or
interval procedure are yet frozen. A different inferential method requires its
own prospective assumptions, not a result-dependent replacement of this one.

Fresh directories do not establish independent draws. Shared memory, server RNG,
decoding, hardware scheduling or rater behavior can remove assumed randomness
or induce dependence. The current client sends no per-request model seed; executor
seeds therefore do not qualify paired model randomness. At the deployment's
reported upstream pin, sampling defaults are copied into each request and a
sampler is initialized from the resulting seed for each sampling task. A fixed
startup seed is thus reused per request, not an advancing cross-request stream;
positive temperature does not resolve the repeatability/independence distinction.
The [source inspection and prospective schedule](../docs/publication_experiments.md#model-randomness-and-the-prospective-schedule)
declare the proposed per-draw startup seeds, pairing and separate data streams.
They establish neither observed sampler state nor cross-block independence.
If cross-block independence is unsupported, do not use the bound. Qualify a
different design or
report descriptive outcomes without a calibrated interval. A purposive roster is
not a probability sample, and family resampling does not create generalization
to unseen statistical research.

## S4. Inner Statistical-Method Simulation

For each task and scenario, the protocol records the aim, DGP, estimand, method
settings and information access, performance measures, replication count or valid
stopping rule, RNG/streams and failure handling. This follows the established
[ADEMP guidance](https://doi.org/10.1002/sim.8086); it is not a new harness recipe.
Diagnostic computation may change the method or argument. Confirmation instead
uses the frozen source, parents, DGP and measures on the specified fresh data.
Shared metadata projection alone does not establish fresh or blinded data.

Let $B$ be the fixed number of independent inner repetitions in one scenario,
$\theta$ its true target, and $b=1,\ldots,B$ index datasets. For method $m$,
let $I_b^m=1$ when a valid finite point estimate $\widehat\theta_b^m$ is
returned, and $J_b^m=1$ when a valid interval $[L_b^m,U_b^m]$ is returned under
the declared method's inference convention. Define $C_b^m=1$ when $J_b^m=1$
and the interval contains $\theta$, and $C_b^m=0$ otherwise. No nonexistent
estimate or interval is evaluated as if it were a numerical output. Let
$M_I^m=\sum_b I_b^m$ and $M_J^m=\sum_b J_b^m$.
Validity follows the predeclared method/output contract, not a favorable outcome.
If a method legitimately returns unbounded confidence sets, specify their
representation and length handling rather than relabel them numerical failures.

The point and interval failure fractions are respectively

$$
\widehat f_I^m=1-M_I^m/B,\qquad
\widehat f_J^m=1-M_J^m/B.
$$

Point-estimate bias conditional on a valid fit is estimated, when $M_I^m>0$, by

$$
\widehat{\operatorname{Bias}}_{\mathrm{valid}}^m
=\frac{1}{M_I^m}\sum_{b:I_b^m=1}(\widehat\theta_b^m-\theta).
$$

Its target is $\mathbb E[\widehat\theta^m-\theta\mid I^m=1]$, not
unconditional bias of an estimator defined on every dataset. With independent
identically distributed repetitions and finite conditional second moment, its
usual plug-in Monte Carlo standard error is $s_m/\sqrt{M_I^m}$ for $M_I^m>1$,
where $s_m$ is the sample standard deviation of the valid estimation errors.
When no fit is valid the bias is unavailable, not zero; with only one valid fit
the sample-based MCSE is unavailable. Method-dependent failures can make this
conditional comparison misleading, so report failure fractions alongside it.

Report two distinct interval summaries:

$$
\widehat p_{\mathrm{return\ and\ cover}}^m
=\frac{1}{B}\sum_{b=1}^B C_b^m,\qquad
\widehat p_{\mathrm{cover}\mid\mathrm{valid}}^m
=\frac{1}{M_J^m}\sum_{b=1}^B C_b^m\quad(M_J^m>0).
$$

The first estimates the probability of successfully returning a covering
interval, counting invalid or absent intervals as unsuccessful delivery. It is
not nominal coverage for an interval undefined on failed datasets. The second
estimates coverage conditional on an interval being valid. It cannot hide the
failure probability or support an unconditional coverage assertion. Mean interval
length is likewise conditional on valid intervals unless a different meaningful
failure loss is prospectively defined. Report its denominator and MCSE.

For an independently repeated Bernoulli measure with probability $p$, the exact
Monte Carlo variance of the empirical proportion satisfies

$$
\begin{aligned}
\operatorname{Var}\!\left(\frac1B\sum_{b=1}^B C_b\right)
&=\frac1{B^2}\operatorname{Var}\!\left(\sum_{b=1}^B C_b\right)
 &&\text{(variance scaling)}\\
&=\frac1{B^2}\sum_{b=1}^B\operatorname{Var}(C_b)
 &&\text{(independent repetitions)}\\
&=\frac1{B^2}\sum_{b=1}^B p(1-p)
 &&\text{(Bernoulli variance)}\\
&=\frac{B p(1-p)}{B^2}
 &&\text{(sum over repetitions)}\\
&=\frac{p(1-p)}{B}
 &&\text{(cancel the common factor).}
\end{aligned}
$$

The plug-in MCSE is $\sqrt{\widehat p(1-\widehat p)/B}$, not a confidence
interval. Boundary proportions need an appropriate prespecified binomial interval;
zero observed events do not certify zero uncertainty. The worst-case standard
error is at most $1/(2\sqrt B)$, so $B\geq1/(4\delta^2)$ suffices for a
standard-error target $\delta>0$ under these assumptions. This is not a
confidence-half-width calculation or a universal replication count. Random
precision-based stopping needs its own qualified rule; repeatedly checking an
ordinary fixed-sample interval does not make it sequentially valid.
The displayed fixed-$B$ formula applies to the all-attempt Bernoulli measure.
Conditional coverage uses the valid-interval denominator $M_J^m$, with its
conditional sampling assumptions stated; it is not given the all-attempt precision.

Where methods use the same datasets, calculate MCSE for the per-dataset paired
difference rather than assume independent methods. For fully observed operational
coverage indicators, use the sample standard deviation of $C_b^m-C_b^{m'}$
divided by $\sqrt B$ under independent dataset repetitions. Pairwise-valid
point-estimate comparisons have a different conditional target and must report
that denominator and both failure fractions. Quantile, tail, variance and other
measures need appropriate uncertainty methods, not automatic use of the
Bernoulli formula. A shared simulation dataset is not an independent agent draw.

## S5. Published-Result Case Qualification

The current candidate is Guo, Zheng and Buhlmann's invalid-instrument work,
[JMLR 27(198), 2026](https://www.jmlr.org/papers/v27/24-0515.html).
Its bounded task uses B1 and Card Appendix E.1, not the entire article. The
paper, author code and application data are visible, so this is source-assisted
replication/reconstruction, not blind rediscovery. The inspected family cannot
be described as a sealed untouched test. The separate JSS software example,
final theory article, simulation grid and application have different scopes.

The case argument must state the treatment-effect estimand, structural model,
violation spaces and relevant assumptions; distinguish identification, estimator
construction, fixed-space inference and selected-space inference; and identify
the published results invoked versus the calculations independently derived.
These arguments must come from the product agents and receive S2 assessment.
This supplement contains no operator-authored replacement proof or numerical gold.

| Component | Required evidence | Present limitation |
| --- | --- | --- |
| B1 inputs | Exact producer, comparators, settings, batch schedule and aggregation | Heteroskedastic comparator helper absent from inspected author sources |
| B1 methods | Oracle TSCI, comparison/robust-selected TSCI, TSLS, oracle RF-Init/Plug/Full; preserve each method's information access | No complete qualified seven-method run or reference |
| B1 output | Declared 18 settings and 25 rounds per setting, each source batch containing 20 repetitions; performance, failures and uncertainty | Source-declared grid/counts, not executed observations |
| Card E.1 | Exact data/covariates, four alternative bases, split/aggregation and interpretation | Original-data rights, aggregate definition and complete execution/reference unresolved; the inspected producer does not record its original RNG sequence |
| Theory | Complete selected explanation with stated assumptions and dependency scope | Independent authority unappointed; source proof findings unresolved |
| Environment | Explicit native Python/R configurations and exact package/library reconstruction across arms | Local mechanisms are verified, not autonomous use or clean release |

The code-to-display mapping and known source gaps are recorded in the evaluator's
[qualification review](../benchmarks/publication_reference_qualification_20261002/tsci_scientific_source_review.md).
That review and reference outcomes must not be supplied as author hints. A
missing required comparator stays missing; no homoskedastic substitute, cached
number or independently written helper becomes unchanged author replication.
Lower-than-nominal published performance is not a replication failure merely
because it is unfavorable. Numerical tolerances and scientific interpretation
are qualified separately before draws.
Missing historical seeds restrict exact replay, not a prospectively specified
stochastic reproduction with its own recorded streams and suitable uncertainty.
A new seed schedule does not supply a missing estimator or aggregation rule.

The application describes log-wage and schooling units, instrument and covariate
choices, its estimand, uncertainty and sensitivity to violation spaces. E.1 is
not automatically the main Figure 4 multi-split analysis. Agreement with a
published estimate cannot establish observational causal assumptions or instrument
validity. No complete case is currently available for a paper's results section.

## S6. Scientific Trace and Resource Accounting

Retain every scheduled draw's identity, task/source access, actual model requests,
stopping cause and final artifact selection. Preserve transport failures, unknown
usage and operator interventions; unknown is not zero. Report setup, reference
qualification, agent execution and external assessment costs separately.
Measured calls, input/output tokens, context/prefill/cache behavior, elapsed time,
scientific compute and hardware condition describe resources. Equal call caps
alone do not equate them. Time-limit stopping needs a stated censored-duration
analysis or clearly labelled observed runtime, not only cost among successes.

Freeze author and evaluator execution conditions separately. Numerical assessment
uses its declared execution profile and records the actual backend and exact
request; an unavailable native environment is not silently replaced with WASM.
Configuration or ABI fixtures establish dispatch, not scientific correctness or
matched access in the study arms.
The [prospective condition follow-up](../benchmarks/publication_case_candidates/published_methods/prospective_conditions_followup.json)
retains the original input edition and binds the proposed execution edition,
native environments, source commands and four-mode configurations. Its settings
are unactivated proposals, not an official schedule or confirmed Monte Carlo
precision. Freeze separate evaluator access and record actual execution before
treating these declarations as qualified scientific conditions.
Current prospective metadata removes an unsupported gap-reporting outcome axis,
not the obligation to report gaps or any substantive task instruction. Earlier
proposal identities and consumed evaluations are preserved at their recorded pins.
For H, all files in predeclared final directories are selected through the
unchanged native snapshot collector, allowing arbitrary local helpers. Missing
directories stay empty; no intermediate selection or content repair is performed.
The native numerical view uses the existing `main.py`/`main.R` project ABI,
with estimator identities, roots and languages fixed before author calls.
It preserves source/helper bytes and passes empirical/reconstruction files
losslessly as base64 bytes, original paths, hashes, lengths and missing-file
inventory. This is transport, not a parser, execution receipt or confirmation
claim. Independent assessment receives the complete captured final submission,
including reports and binary ancillary files. Invalid or missing material is
retained rather than repaired or replaced. The numerical interpretation and
endpoints must still be qualified and frozen identically within each study's
arms; H's file view and S's checkpoint-derived view are not equivalent scientific
conditions merely because their evaluator entrypoint is shared.
The separate same-host workspaces and mock request checks are preparation evidence,
not native agent research, qualified numerical adjudication or a release study.

Case trace analysis identifies a finding, its exact source/input version, the
source owner's response, the revised artifact and independent final outcome.
Label whether a change addresses a real scientific issue or merely produces
valid syntax. Account for unchanged, failed and unresolved revisions. This
explains observed behavior; message counts or selected success traces are not
additional causal evidence beyond the declared arm comparison.

No source, result, selected artifact or consumed assessment is edited to improve
a run. Tables use exact final selections and actual records. Human preparation
and author reference execution are not relabelled autonomous agent contributions.

## S7. Optional Formal and Library Materials

### S7.1. Proposed Import Scope

The supporting library is downstream of the pinned Statlib inference and QMD
APIs, not a competing statistical vocabulary. The proposed compact import scope
contains deterministic-risk and mean-zero-score consumers, a raw-second-moment
identity, L1-bracketing GC conclusions, three L2-bracketing maximal inequalities
and the entropic-barrier theorem. These are existing library materials selected
by the operator; they are not newly produced agent outcomes. Exact modules,
declarations, hypotheses, proof routes and verification identities are in the
[source-bound import selection](../docs/publication_lean_integration_20261002.md#candidate-import-scope-for-the-shared-appendix-2026-10-04).
It remains a candidate selection pending independent source-fidelity and release
review, not a claim of three completed textbooks or a representative coverage
estimate.

The distinctions in that selection matter mathematically. The book-style GC
predicate is disjunctive and its checked theorem uses outer-almost-sure
convergence; the selected direct outer-probability theorem additionally requires
countability, measurable class functions and a finite sampling measure. The L2
inequalities use the centered `sqrt(n) (P_n-P)` process, an extended floored-log
bracketing entropy integral, explicit envelope/localization assumptions and
separate infinite-entropy cases. Their explicit constants are not claimed sharp.
The entropic-barrier selection does not include the source's universal-barrier
claim. Kernel checking these precise statements cannot remove their hypotheses
or establish faithful correspondence to every source result.

### S7.2. Evidence And Comparison Boundary

A formal result identifies the informal source statement, Lean target, imports,
dependencies, active project/toolchain pins, exact submitted file, fresh kernel
check and allowed axioms. Source correspondence is reviewed independently of
compilation. Retrieval supplies candidate premises; an inaccessible declaration
or target-proof leakage invalidates the intended retrieval comparison.

If a prover comparison is claimed, specify supplied-Lean versus informal-target
tasks separately, use matched zero-shot, compile-feedback and compile-plus-RAG
conditions, and qualify any external implementation with its actual model/project
adaptations. Do not compare unrelated published success rates. Such comparisons
are not required to finish the non-formal statistical research study.

The shared EmpericalProcessLEAN support report needs a defined scoped source
inventory, declaration mapping, dependency/axiom status, rights and human/agent
attribution. Counts and author-maintained labels are not source coverage. Existing
selected checks and unsuccessful migration/reconstruction attempts retain their
own scopes. Library evidence is documented once and cited by both papers, not
counted twice as autonomous research or proving results.

## S8. Manuscript Placement and Result Material

This map specifies required output, not empty result tables. Table/figure labels
are provisional; final numbering follows the completed manuscript. Every reported
value needs a licensed input, exact record and reproducible analysis path.

| Location | Paper H | Paper S | Acceptance evidence |
| --- | --- | --- | --- |
| Sections 1--2 | Scientific purpose, closest portable packages, actual package/host boundary | Scientific question, closest research agents, actual graph/roles/source ownership | Verified code scope and attributable primary sources |
| Sections 3--4 | Fixed-host intervention, uptake, endpoints and S1--S4 analysis | Four-arm interventions, matched conditions and S1--S4 analysis | Frozen prospective tasks, authority and conditions |
| Main results table | Bare/package full-task outcomes and component/failure counts | All four arms with prespecified contrasts and component/failure counts | All scheduled draws and resolved common assessments |
| Resource figure/table | Scientific outcomes alongside uptake, calls/tokens/time/compute | Scientific outcomes alongside all-role cost and stopping/re-entry causes | Complete observed denominators; unknown/censored values labelled |
| Section 5 case | Actual host-with/without-package deliverables and scientific interpretation | Actual specialist findings/revisions, final method and scientific interpretation | Complete case argument, execution and independent assessment |
| Discussion/abstract | Observed incremental value, host/model limits, usability not assumed | Observed bundle effects, correlated errors and ablation limits | Claims bounded by results, not expected improvements |
| Theory appendix | S2/S3 plus complete selected and assessed case arguments | S2/S3 plus complete selected and assessed case arguments | Defined assumptions, every substantive inference and localized review |
| Experiment appendix | Roster/access, exact host/package/model, schedule, all outcomes | Roster/access, roles/tools/transitions, model, schedule, all outcomes | Complete reproducibility and no hidden condition mismatch |
| Simulation/case appendix | S4/S5, full source/DGP/aggregation and application materials | S4/S5, full source/DGP/aggregation and application materials | Per-repetition results, failures, uncertainty and source attribution |
| Lean/release appendix | S7 and qualified host/setup reconstruction | S7 and qualified standalone/setup reconstruction | Scoped compiled support, rights and clean researcher workflows |

The full delivery checklist is maintained in the
[publication programme](../docs/publication_programme.md#delivery-checklist).
Results, full case arguments, task assessment records and release qualification
are not yet available; writing this methods appendix does not complete them.

## References

The [shared scholarly bibliography](references.bib) supplies the journal editions
for Hoeffding's inequality, the ADEMP simulation reference, TSCI and the three
candidate software articles, together with the fixed agent-paper versions cited
by the main texts. Bibliographic checks do not certify an argument, reference
implementation, reproduction result or independent scientific assessment.
