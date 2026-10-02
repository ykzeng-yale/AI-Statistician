# AI-Statistician: Scoped Collaboration for Statistical Research Through a Single Model API

Working methods draft, 2026-10-02. Not submission-ready. Authors and affiliations
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
does not establish independently concurrent computation. Parallel work and
exact-input joins are an unfinished implementation requirement, not a reported
speed advantage. The Architect resolves initial evidence needs and genuine
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

The current scientific executor uses pinned Pyodide and webR environments in
bounded local subprocesses. An explicitly configured offline native project tool
is separate. These tools do not establish arbitrary dependency reconstruction,
clean-machine replication or the ability to run every published scientific
package. Missing execution capabilities remain visible instead of silently
falling back to an unrestricted interpreter.

### 2.3. Review and Progressive Commitment

Independent product reviewers receive immutable, scope-bound artifacts in their
own sessions and return findings without editing the source. Theory and exact
implementation review serve different purposes. The source owner decides the
revision. Same-base-model independence is session separation, not independence
of reasoning errors; the final scientific assessment must account for correlated
author/reviewer failure.

Exploratory implementation can begin before all theory is settled and can return
counterexamples or interface findings to TheoryDeveloper. Stable claims and exact
source then receive review. Confirmatory execution freezes source, relevant
parents, protocol and a fresh cohort before outcomes. A result cannot repair its
own acceptance criteria. The simulation design must specify the scientific aim,
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
policy. This intervention isolates reverse graph work only under the declared
submission contract; it also changes author opportunities and can terminate an
arm before final selection. It does not identify a pure effect of criticism
quality at equal source attempts.

Current controls and production have different cohort allocation and some
execution behavior. These must be matched or prospectively declared before
activating comparisons. The common request cap already counts planning and
review calls, but does not equalize tokens, context, runtime or scientific
computation. Resource curves require frozen global conditions and complete
measurement, including failed and usage-unknown requests. No cap or stronger
model is added after seeing a draw's outcome.

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

The independent sampling unit is a paper/problem family. Variants and repeated
draws within one family do not increase the count of independently sampled
problems. Task selection will cover distinct inferential domains and Python/R
work, progressing from known results and replication to hidden derivation and
extensions. Scientific tolerances, draw schedules, failure handling, sample size
and analysis must be frozen prospectively. Family-level paired effects and
uncertainty, rather than rubric-item counts treated as independent samples, will
support the comparison.

## 4. Current Evidence and Limitations

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

Completion requires fresh qualified tasks and gold, matched arm conditions,
complete outcomes and scientifically defensible uncertainty. Independent
concurrency, general environment reconstruction, a curated source-faithful Lean
API, release licensing and source-asset rights remain unfinished. A small
quantized Qwen development configuration cannot support a general capacity claim
about open-weight research models. No superiority, novelty or frontier-discovery
claim is made before the corresponding evidence exists.

## Reproducibility Sources

Architecture and operative policies are specified in
[production design](../docs/production_design.md). The prospective study details
and actual draw entries are in the [experiment specification](../docs/publication_experiments.md).
The [publication programme](../docs/publication_programme.md) separates this paper
from the portable intervention. Exact code, model/runtime/template, source,
environment, task and authority pins must accompany future results; private
credentials and model reasoning are not public trajectory artifacts.
