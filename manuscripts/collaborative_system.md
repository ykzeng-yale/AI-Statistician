# AI-Statistician: Scoped Collaboration for Statistical Research Through a Single Model API

Working methods draft, 2026-10-04. Not submission-ready. Authors and affiliations
are not yet supplied. Official comparative experiments have not been activated;
this draft makes no claim that collaboration improves scientific correctness.

## Abstract

Statistical research joins theoretical reasoning, implementation and experimental
assessment, which can fail even when each generated artifact appears plausible.
We describe AI-Statistician, a system in which specialist research sessions share
hash-bound artifacts through one typed research graph and one retained model/tool
loop. The source-owning model receives raw execution or reviewer observations
and authors every revision; the runtime supplies identity, execution and evidence
boundaries rather than statistical answers or repair rules. Theory is maintained
in Markdown/LaTeX, scientific work uses Python/R, and Lean is selected by task
intent. We specify a four-arm open-weight comparison separating free planning,
shared-context workflow, role-separated work without reverse revision, and full
collaboration. Independent final-artifact evaluation is common to all arms and
does not use the system's internal acceptance as scientific truth. Comparative
effects and their uncertainty remain to be measured.

## 1. Research Question

The relevant question is not whether several named agents can produce a report.
It is whether scoped collaboration improves independently accepted statistical
research outcomes over one capable source-owning agent with comparable tools
and resources. A reviewer can expose a missing assumption or estimator mismatch,
but additional sessions also consume context, calls and time and can repeat a
shared model error. Controlled agent-system work reports task-dependent benefits
and costs rather than a universal advantage of additional agents. [Kim et al.](https://arxiv.org/abs/2512.08296)
Evaluation therefore separates architectural effects from model choice and
resource allocation, consistent with the concerns in [AI Agents That Matter](https://arxiv.org/abs/2407.01502).

The neighboring literature measures different targets. PaperBench evaluates
research replication and separately evaluates its grader. Fisher-R1 studies
executed hypothesis testing against reference p-values and decisions. Neither
endpoint alone measures whether a research agent develops a complete, correct
statistical argument. Our proposed comparison adds assessment of the argument,
its exact implementation and empirical interpretation; that assessment has not
yet been qualified or run. [PaperBench](https://arxiv.org/abs/2504.01848),
[Fisher-R1](https://arxiv.org/abs/2608.07437)

VERITAS supplies a closer statistical-analysis comparison, including a
phase-guided single-agent arm. Its local role configuration uses different
checkpoints, so its reported effects do not isolate our same-model question.
LabAgent separately studies laboratory reproduction and memory. Neither supplies
our independent statistical-derivation outcome. [VERITAS](https://arxiv.org/abs/2604.12144),
[LabAgent](https://arxiv.org/abs/2609.13437)

The statistical task is defined by its inferential target and evidence needs.
Identification, estimation, computation and inference are different obligations.
Published-code replication is not the same task as deriving a theorem from
background definitions; historical rediscovery does not remove pretraining
contamination. The system may establish a conditional claim, find a counterexample
or report an unresolved gap rather than manufacture a positive result.

The portable package described in the companion methods draft is a different
intervention. It adds guidance to a researcher's existing host. AI-Statistician
instead drives its own specialist sessions from one model API and does not call
Codex or Claude Code to conduct the research. Shared implementation and library
artifacts are disclosed; the same experiment is not presented twice as independent
evidence for these two questions.

## 2. System Implementation

### 2.1. One Graph and One Tool Loop

`AgentRuntime` is the sole outer research graph. It holds tasks, selected artifacts,
pending work and evidence dispositions. `client_tool_loop` is the retained
model/tool loop configured by Theory, scientific-code, Simulation, Lean and
reviewer workspaces. There is no second scheduler, generic agent framework or
runtime-generated source repair. A model action is executed under the workspace's
actual permissions, and its observation returns to the same source owner.

The current outer execution is serial/interleaved. A dual-track dependency policy
does not establish independently concurrent computation. Independently concurrent
work would require dependency-aware scheduling and exact-input joins; it is not
a measured intervention in the current proposal or a reported speed advantage.
The Architect resolves initial evidence needs and genuine
cross-workspace conflicts; ordinary source/compiler errors stay in the owner's
retained workspace rather than require another planning round.

Tasks and durable traces use references. Substantive mathematics, code and Lean
files have content-bound identities. An artifact selection records the actual
producer and relevant consumed inputs; a later change invalidates dependent
evidence without requiring unrelated work to be repeated. A hash demonstrates
byte identity, not correctness or integrity against an adversarial host.

### 2.2. Theory and Scientific Source Ownership

TheoryDeveloper maintains definitions, assumptions, equation chains and dependent
claims in Markdown/LaTeX files. Compact handoffs identify claims and executable
interfaces, not duplicated mathematical prose. The model can search permitted
literature and code, inspect versioned source, edit a local derivation, run
Python/R scratch work, commit a checkpoint or report a gap. Structural validity
does not establish mathematical maturity or force a successful conclusion.

Algorithm and Simulation owners use the same loop to write or edit exact Python/R
source, execute it, inspect raw observations and revise it. Multi-file projects
retain support-file identities. Every execution attempt has a separate stored
request, exact source and logs; identical computational inputs do not overwrite
earlier failure evidence. The runtime does not infer a statistical answer from
an error message or inject a hand-written fix into model-authored code.

The default scientific executor uses pinned Pyodide and webR in bounded local
subprocesses. Explicit native Python/R profiles reuse their existing ABIs and one
pinned local executor; installed packages come from the operator's environment,
not task rules. Raw observations return to the source owner without automatic
backend fallback. Native execution currently requires macOS isolation. Configured
interpreter/package versions are checked before source execution; they do not
establish frozen package bytes. The installed native Python environment determines
import access; a declared dependency list is not its security boundary. The offline native project tool
is separate. Local execution fixtures establish these mechanism scopes, not
autonomous use, arbitrary dependency reconstruction or clean-machine replication.
Network is denied by default. Explicit operator-selected worker ports permit
listening and loopback-only outbound connections on those ports; listeners can
bind all interfaces, so this is not loopback-only inbound isolation. This optional
permission is a frozen execution condition, not model-owned escalation. Two-worker
FORK/PSOCK conformance does not establish parallel research-agent execution or a
scientific speed advantage.

### 2.3. Review and Progressive Commitment

Independent product reviewers receive immutable, scope-bound artifacts in their
own sessions and return findings without editing the source. Theory and exact
implementation review serve different purposes. The source owner decides the
revision. Same-base-model independence is session separation, not independence
of reasoning errors; the final scientific assessment must account for correlated
author/reviewer failure.

Exploratory implementation can begin before all theory is settled and can return
counterexamples or interface findings to TheoryDeveloper. Stable claims and exact
source then receive review. The intended confirmatory contract freezes source,
relevant parents, protocol and fresh data before outcomes. Current default seed
initialization does not itself establish data freshness; Section 4.1 records the
qualification still needed. A result cannot repair its own acceptance criteria.
The simulation design must specify the scientific aim,
DGP, estimand, method, measure and Monte Carlo uncertainty rather than use a
universal repetition count. [Morris et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/)

Internal acceptance is a product disposition under that task's evidence contract.
It is not a common external correctness measure, especially when a comparison
arm has no isolated product reviewer. External gold is never supplied to source
owners and is applied only after the actual final selection has terminated.

### 2.4. Lean and Shared Mathematical Foundation

Formalization is optional, advisory or required according to frozen task intent.
A stable target can use active-project declaration retrieval and real Lean
diagnostics in the same source-owner loop. An optional formal gap remains visible
without erasing accepted non-formal evidence. A required formal task cannot lower
that requirement because proving is difficult.
Optional Lean does not remove the obligation to justify a theoretical claim with
a complete mathematical argument and independent assessment.

Lean checks establish the encoded statement. Exact target identity, fresh
compiled dependencies and an allowed-axiom audit are required for formal evidence;
correspondence to the requested informal theorem also requires semantic scrutiny.
LeanDojo's accessible-premise and verified-feedback design is relevant prior art,
not evidence for this system's proving performance. [LeanDojo](https://arxiv.org/abs/2306.15626)

EmpericalProcessLEAN supplies the pinned Mathlib/Statlib foundation and downstream
StatInference library. The active foundation remains Lean 4.30.0 until a separately
tested migration succeeds. Source-map labels, declaration counts and selected
kernel checks do not establish complete textbook formalization. Upstream Statlib
roadmaps and incompatible declarations are not active proof premises. Both papers
will report library scope, mathematical attribution and unresolved source rights
separately from new agent outcomes.

## 3. Prospective Comparative Study

### 3.1. Arms and Attribution

The implemented draw entries configure four conditions on the same local base
model. The free-planning control exposes the actual production-backed research
actions in one conversation without prescribed role order. A second control adds
the prospectively fixed workflow in that same context. Review actions in either
control are shared self-review, not independent receipts.

The role-separated reverse-revision ablation uses the production graph and
reviewers but withholds another role's return to a previously visited source
owner or its typed environment-feedback route. Forward review, same-owner local
feedback and an exact accepted-source return to its deferred execution phase
remain available. Full collaboration uses the unchanged production handoff
policy. The ablation stops the graph when prohibited re-entry is requested and
can therefore prevent a final selection. Its contrast measures the operational
value of allowing reverse revision rather than this blocking/early-stop policy,
not feedback content alone at equal author attempts. Such stops stay in the
denominator; earlier drafts are not promoted or routed around review to make
the arm finish.

Full collaboration versus free planning evaluates the implemented product bundle.
The shared-context workflow contrast evaluates added fixed guidance, once other
conditions match. Full collaboration versus that control additionally changes
role contexts, routing, product-review authority and revision opportunities; it
does not isolate context separation alone. The four arms do not separately
identify independent-review, durable-memory or Lean effects.

Current controls and production have different cohort allocation and some
execution behavior. These must be matched or prospectively declared before
activating comparisons. The common request cap already counts planning and
review calls, but does not equalize tokens, context, runtime or scientific
computation. Resource curves require frozen global conditions and complete
measurement, including failed and usage-unknown requests. No cap or stronger
model is added after seeing a draw's outcome.

All four preparations now supply the research-evaluation Theory policy and the
same Python/R scratch tool schemas. Effective output limits still depend on the
entry: production Theory uses its serious-mode limit, while the shared session
uses its request limit. These values must be matched explicitly. This corrects
an initial context difference; it does not make whole prompts, confirmation
exposure or realized resources identical.

The unactivated case candidate now aligns required-tool turns across the shared
session and retained specialist workspaces. This controls an avoidable request
policy difference, not the research sequence. Integrated production first requests
a structured Architect plan; the shared session can plan through its ordinary
tools. Shared turns permit batching, while scientific-source specialists use
single-call turns. These transport and opportunity differences remain part of
the declared product bundle, not an isolated test of role separation.

Evaluator-owned cohort and transition metadata have a separate model-visible
projection, used by the Architect, code reviewer and Theory feedback files.
The same projection is applied to scientific-owner context and observation views.
The stored originals remain available for audit. This does not sanitize raw
source output: executed code or a referee document can disclose a seed in text,
and later data streams can remain predictable. Metadata withholding therefore
does not by itself establish blinded, outcome-independent confirmation. The
study must qualify its actual source and feedback exposure rather than treat
this projection as a scientific guarantee.
Model-visible history reads use the same metadata projection while leaving the
full stored observations and checkpoint payloads unchanged. The selected raw
record and returned view have separate hashes. This does not confer retrospective
blinding on older sessions or sanitise author-visible text.
Runtime-seed projection requires explicit evaluator ownership; an ordinary
research observation is not private merely because it has that field name.

### 3.2. Common External Outcome

Trusted final readers collect only the terminated run's selected artifacts.
`publication_material_from_submission` projects exact Theory documents,
estimator bindings and submitted simulation rows. The common evaluator inspects
those artifacts without requiring internal acceptance or product-role review.
Missing material stays missing; an earlier passing draft cannot be salvaged as
a final result. Executable implementation checks and submitted experiment checks
are separate, so a correct estimator cannot manufacture an absent experiment.

The primary endpoint is independently accepted full-task output for the frozen
intent. Mathematical acceptance requires qualified authority and a hidden claim
rubric. An executable reference can judge numerical reproduction but not a proof.
PaperBench's replication evaluation motivates artifact-level assessment, while
statistical derivations require additional mathematical scrutiny. [PaperBench](https://arxiv.org/abs/2504.01848)
Optional formal outcomes remain separately reported.

For the theoretical endpoint, a prospectively frozen authority supplies its
assessment of the actual selected argument and an explicit accepted, rejected
or unresolved conclusion. The evaluator binds the report to the frozen task,
final submission and complete material and stores its exact bytes and protocol.
It does not create a mathematical referee, infer a verdict from prose or certify
expertise through a hash. Missing assessment remains pending; unresolved theory
does not satisfy full-task acceptance. Local-model grading remains a separately
labelled automatic diagnostic, not a substitute for this independent endpoint.
The available tests establish record identity and non-substitution only; no
qualified panel or mathematical acceptance has yet been demonstrated.

Numerical assessment likewise uses exact selected material. The common
runtime/shared-control view now includes complete declared source-result and
execution-stream bytes, not only file hashes or truncated previews. Missing
results and failed executions remain visible; earlier attempts are retained as
lineage, not substituted outcomes. This enables format-specific evaluation but
does not qualify a parser, numerical tolerance, simulation uncertainty rule or
reference convention. Those belong to the prospective task authority. Python/R
artifact checks use the existing executor and a fixed `evaluate_artifact` entry.
R's explicitly configured native environment can read captured RDS/RData without
Python conversion. An unavailable dependency/profile reports failure rather than
selecting another backend. This mechanism does not appoint a numerical assessor
or validate a statistical method.

The task-selection and possible generalization unit is a paper/problem family.
Variants and repeated draws within one family do not add new sampled problems.
The proposed roster is purposive, not a probability sample. Task selection will
cover distinct inferential domains and Python/R work. The broader capability
strategy progresses from replication to hidden derivation and extensions, but
those later conditions are not observations in the present source-assisted
proposal. Scientific tolerances, draw schedules, failure handling, sample size
and analysis must be frozen prospectively. Family-level paired effects and
uncertainty, rather than rubric-item counts treated as independent samples, will
support the comparison.

The current [candidate task definitions](../benchmarks/publication_case_candidates/published_methods/README.md)
cover StepMix external-variable methods, ebnm prior-family comparison and
bizicount joint count regression. They require theoretical argument, scientific
source and empirical analysis together under declared paper/code access, not
merely source execution. They are source-assisted reconstructions, not tests of
unknown-theorem discovery. Existing EM/normal-means exposure and the common
software-journal source channel remain limitations. Independent argument authority,
input/ABI and arm qualification, rights and the roster/precision freeze are still
pending; these definitions provide no collaborative effect estimate.

The unactivated [condition follow-up](../benchmarks/publication_case_candidates/published_methods/prospective_conditions_followup.json)
binds public estimator transport metadata and all twelve proposed configurations
to existing local Python/R and source profiles. It supplies no method formula or
scientific acceptance endpoint. Static references and explicit resource proposals
do not establish observed arm matching, adequate resources or efficacy.
Preparation now rejects active outcome dimensions the common evaluator cannot
assess. Gap reporting remains a scientific obligation, not a fabricated score.
The original unactivated proposal and all consumed observations remain archived.

The source-only replication entry currently exercises TheoryDeveloper, not the
Theory/code/Simulation collaboration under study. It can support a reproduction
component check but cannot identify the effect of reverse specialist feedback.
The main collaboration tasks must actually require and expose that interaction
under the same objective in every arm. This is a study-design requirement, not
a reason to invent extra roles, mandatory review rounds or theorem-specific rules.

## 4. Simulation and Statistical Analysis

### 4.1. Agent-System Comparison

The proposed primary estimand is the full-collaboration-minus-free-planning
difference in expected independent full-task acceptance on a fixed qualified
benchmark, under one frozen base-model and resource condition. The same-workflow
comparison assesses fixed guidance within one conversation. Its comparison with
full collaboration assesses the additional product bundle, not session separation
alone. The reverse-revision comparison includes its blocking/early-stop policy;
it does not by itself identify the effect of reviewer intelligence.
Primary and secondary contrasts must be fixed before examining outcomes rather
than chosen from whichever arm difference is largest.

Each family receives the same access condition and scheduled paired draws across
arms in separate clean workspaces. One prespecified primary task/access condition
per family defines the initial comparison; variants require declared within-family
aggregation. With frozen weights $w_i>0$, $\sum_i w_i=1$, scheduled draw
counts $R_i$, and independently adjudicated full-task acceptance indicators $Y_{ir}^a$,
the aggregate estimate is

$$
\widehat\Delta_{\mathcal B}^{\mathrm{full},\mathrm{free}}
=\sum_{i=1}^N\frac{w_i}{R_i}\sum_{r=1}^{R_i}
 (Y_{ir}^{\mathrm{full}}-Y_{ir}^{\mathrm{free}}).
$$

Here $\mathcal B$ is the fixed roster; equal-family weights are $1/N$.
The indices $i$, $r$ and $a$ denote family, scheduled draw and arm.
Report family outcomes before aggregation. Inner simulation repetitions and
individual findings are not outer agent draws. Repeated runs estimate variation
under the frozen run mechanism, not task-population uncertainty. In particular,
executor/data seeds are not model seeds: the current model client does not send
a per-request seed. Decoding, RNG behavior and run independence need prospective
qualification. Family resampling cannot turn a purposive roster into a sample
of arbitrary statistical research. Appendix B specifies the conditional target
and uncertainty requirements; official counts and the analysis remain unfrozen.

Common tools, accessible sources, experimental data and meaningful resource
conditions are necessary for attribution. Total calls alone do not equate total
context, generated tokens, computation or review effort. Report measured model,
tool and scientific execution costs for every scheduled draw and disclose any
remaining mismatch. A secondary quality-resource study, if undertaken, fixes its
conditions beforehand; post-outcome cap changes are not part of the same comparison.

The current implementation audit finds material conditions that still require
prospective qualification. Both shared controls now expose the production
Python/R Theory scratch tools, but execution timeouts, exploratory data streams,
private confirmation capacity and outcome exposure must be matched or declared.
Simulation authoring intent and diagnostics now use the public research seed,
not a transformation of the private confirmation seed.
The product's default confirmation seed can equal its public exploratory seed;
redacting cohort metadata does not make those data fresh or independent.
Confirmation feedback also differs between a shared conversation and isolated
source-owner sessions. The operational settings and remaining differences are
listed in `docs/publication_experiments.md`; arm names and equal request caps do
not establish comparability. No study is activated by this tool-conformance work.

Failure reporting distinguishes an invalid derivation, an implementation error,
an unmet task condition, missing final selection and environmental interruption.
The primary intention-to-evaluate denominator retains them all. Internal acceptance
and the external mathematical verdict are shown separately; their disagreement
is not resolved by changing the external rubric. Conditional quality among produced
artifacts is descriptive and does not replace the full-task endpoint.

### 4.2. Statistical-Method Simulation Within a Draw

The agent's generated method has its own estimand and simulation design. Its
protocol must name the aim, DGP, estimand, competing methods and performance
measures, with justified finite-sample and assumption-departure settings. Outcomes
can include error, coverage, type-I error, power or other task-appropriate measures;
these are not interchangeable. Monte Carlo uncertainty, invalid fits and failure
handling accompany each measure. Common generated datasets can support paired
method comparisons where appropriate. [Morris et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/)

These inner repetitions evaluate one statistical procedure under specified DGPs.
They are not repetitions of the research agent and do not establish mathematical
correctness, novelty or a system-level success rate. A numerical diagnostic can
challenge a claim. Numerical agreement cannot establish a general proof, and a
disagreement requires investigation rather than an automatic theorem verdict.
Exploratory computation may change theory; confirmatory source, comparisons,
metrics and precision or valid stopping conditions are fixed before results.

Mathematical assessment instead reads the complete selected argument. An expert
checks every substantive inference and the conditions of invoked results, including
normalization, rates and any change of hypotheses. Each invalid or incomplete
claim receives a localized finding rather than a vote from the author's model.
Alternative proofs and legitimate negative conclusions are evaluated under the
frozen task intent. A manuscript, executable code and simulation table that tell
different scientific stories do not constitute an accepted research result.

## 5. Scientific Case Study and Collaboration Analysis

The case is selected before outcomes for a substantive inferential difficulty,
available source/data rights and independently assessable conclusions, not because
it yields a polished report. It must specify the population, estimand, assumptions,
baseline analysis and practical question. For an existing method, report what
has been reproduced and what extension is actually attempted. A new theoretical
claim requires a complete argument; a reproduced table is not such a claim.
No case currently meets the full publication contract.

The current invalid-instrument candidate illustrates why task scope matters.
Its [source qualification](../benchmarks/publication_reference_qualification_20261002/tsci_scientific_source_review.md)
distinguishes software-output reproduction, independent argument assessment and
a substantive research task using specialist feedback. Only the last can test
the proposed collaboration mechanism. A TheoryDeveloper-only reproduction does
not become a multi-agent experiment by changing its arm label. If this candidate
is selected, actual specialist inputs, source-owner revisions and common external
assessment must be specified before runs. The shared source review is preparation
for both papers, not two independent results or completed case evidence.

The main scientific account will connect the actual derivation to the generated
method, simulation or data analysis, comparisons, uncertainty and interpretation.
It will retain unresolved assumptions and sensitivities that affect the result.
The companion behavioral analysis will use exact artifact versions and raw
observations to identify whether a specialist finding exposed a real scientific
problem, whether the source owner revised it, and whether the final outcome
survived external assessment. Message volume or reviewer agreement is not a
mechanism benefit. This trace analysis is explanatory, not an independent causal
estimate beyond the randomized or paired arm comparison.

All prespecified cases and interventions are reported, including failure to
finish, source adaptations and any human selection of ideas or runs. AI Scientist-v2
discloses such selection and its own code/manuscript discrepancies; autonomous
activity within a selected run does not remove selection bias from a success-rate
claim. [AI Scientist-v2](https://arxiv.org/abs/2504.08066)
Complete case artifacts belong in the supplement, while scientifically essential
results and limitations remain in the main paper.

## 6. Current Evidence and Limitations

No official four-arm scientific effect has been estimated. The earlier Qwen
development panel used one family, produced no final selection and had unmatched
conditions and incomplete mathematical authority. Those outcomes are preserved,
not resumed, rescored or used as publication efficacy evidence. Haiku development
records likewise remain outside official results and baselines.

Mechanism tests cover artifact identity, observations, owner iteration and
evaluation boundaries. They do not establish derivation correctness or autonomous
research capability. Selected library checks are not an agent proof success
rate. Native host compatibility belongs to the portable-package study rather
than this system's comparative scientific endpoint.

The preserved development record also contains internal acceptance followed by
independent full-task rejection, and automated acceptance that missed an explicit
task restriction. These observations motivate external assessment; they are not
a new comparative result or a reason to regrade the consumed runs.
[Trimmed-mean record](../docs/operator_audits/trimmed_mean_l0_v1.md),
[betareg record](../docs/operator_audits/betareg_gasoline_precision_l1_v1.md)

Completion requires fresh qualified tasks and gold, matched arm conditions,
complete outcomes and scientifically defensible uncertainty. Independent
concurrency, general environment reconstruction, a curated source-faithful Lean
API, release licensing and source-asset rights remain unfinished. A small
quantized Qwen development configuration cannot support a general capacity claim
about open-weight research models. No superiority, novelty or frontier-discovery
claim is made before the corresponding evidence exists.

The system paper does not require a cosmetic new statistical theorem. Its
architectural contribution must instead be supported by a defensible comparison
and useful scientific outcomes. If independent assessment finds no benefit, that
result constrains the claim; it is not repaired by changing tasks or hiding failed
draws. Additional software capability, model training or library growth would be
separate contributions needing separate evidence.

## Appendix A. Theory Assessment and Complete Arguments

For each theoretical task, supply the exact definitions, hypotheses, selected
claims, lemma dependencies and complete Markdown/LaTeX argument. Calculations
are presented as vertical equation chains, changing one justified subpart per
line, with conditions and the appropriate equality, implication, bound or limit
symbol. The reference theorem is not a premise for its own rederivation. A full
proof appendix, not a familiar formula or finite simulation, supports mathematical
acceptance. Disproved, conditional, conjectural and unresolved results are labelled
according to the actual argument.

The assessment record will specify the hidden rubric, acceptable alternative
arguments, scope-changing errors, independent reviewer qualifications, blinding,
conflicts and adjudication. If an automated judge is used, its assessment against
independent mathematical annotations is reported separately. Reviewer reliability
and unresolved cases must not disappear into a single acceptance field. These
materials are not yet qualified for the official study.

## Appendix B. Full Comparative Protocol and Outcomes

Supply the task-family inventory, selection/exclusion rules, access horizons,
split, model/weight/runtime/template pins, prompts and role tool permissions.
Document each arm's actual transitions, review independence, source-revision
opportunities, context and resource condition; diagram labels are insufficient.
Freeze the schedule, endpoints and analysis before calls, and release all scheduled
draw outcomes, costs, stopping causes, final selections and operator interventions.
No missing final result is replaced by an intermediate artifact.

The [analysis specification](../docs/publication_experiments.md#outcomes-and-analysis)
defines the expected acceptance target conditional on the fixed benchmark and
run conditions. It derives the estimator's expectation by linearity and gives a
conservative bounded-sum interval only under independent paired run blocks.
Dependence within a pair is allowed; cross-draw dependence or unqualified grading
cannot be removed by that calculation. Planned weights, repetitions, contrasts,
multiplicity and the actual RNG/scheduling design must be supplied before draws.
Inference for a population of new tasks would require a separate sampling design.
These are evaluation methods, not a new theorem about scientific correctness.
The full calculations have one source in
[Supplement S3](supplementary_methods.md#s3-fixed-benchmark-target-and-conditional-uncertainty).
Its standard expectation identity requires no run independence; the confidence
bound does. Pending external assessment is not silently treated as an adverse
expert judgment or a completed official outcome.

Scientific-code replication requires the exact generated source and support files,
environment, DGP, comparator settings, random-number handling, Monte Carlo precision
and failures. Main and supplementary tables/figures must be reproducible from the
same released results. Human-prepared references and development diagnostics are
labelled separately from autonomous agent execution. Private model reasoning and
credentials are not required public artifacts.

## Appendix C. Complete Case and Optional Formal Evidence

The case supplement contains the complete argument, implementation, analysis and
scientifically relevant feedback/revision trace, including contradictions and
negative outcomes. It allows assessment of whether the argument, code and reported
conclusions agree, rather than only showing an attractive trajectory excerpt.

Lean claims additionally require exact targets, source-statement correspondence,
imports/dependencies, active-project pins, kernel checks and allowed axioms. A
library source map needs a defined coverage inventory and reviewed mappings before
coverage is estimated. Reused, human-authored and agent-produced results are
attributed separately. The shared foundation is documented once and referenced
by both studies, not counted twice as independent agent performance. Non-formal
tasks do not acquire an additional Lean completion gate through this appendix.

## Reproducibility Sources

Architecture and operative policies are specified in
[production design](../docs/production_design.md). The prospective study details
and actual draw entries are in the [experiment specification](../docs/publication_experiments.md).
The [publication programme](../docs/publication_programme.md) separates this paper
from the portable intervention. Exact code, model/runtime/template, source,
environment, task and authority pins must accompany future results; private
credentials and model reasoning are not public trajectory artifacts.
