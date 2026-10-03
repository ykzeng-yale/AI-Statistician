# A Portable Harness for Reviewable Statistical Research with Coding Agents

Working methods draft, 2026-10-02. Not submission-ready. Authors and affiliations
are not yet supplied. Comparative results, usability results and release rights
remain unresolved; this draft does not claim an efficacy result.

## Abstract

Statistical methods research requires more than executable code. The inferential
target, assumptions and derivation must agree with the implemented procedure,
and simulation results must be interpreted under a specified design. We describe
a portable statistical-research package that works through a researcher's existing
coding agent rather than supplying a second agent controller. The package keeps
mathematics in reviewable Markdown or LaTeX, uses native file and execution tools
for Python/R work, and selects Lean verification according to the research task.
Its operating guidance distinguishes exploration, independent review, confirmation
and exact formal evidence. We specify separate tests of native installation,
scientific outcomes and researcher effort. Scientific comparisons are prospective
and use pinned open-weight models; their results are not yet available. Native
compatibility observations alone do not establish improved research performance.

## 1. Scientific Purpose and Related Work

A statistical research claim concerns an estimand under explicit assumptions.
Correct program execution does not establish identification, a valid asymptotic
argument or calibrated inference. Conversely, a formalization failure need not
invalidate a correctly reproduced numerical analysis. A usable research assistant
must preserve these distinctions while allowing theory and computation to inform
each other.

Simulation reporting provides an established scientific standard, not a new
contribution of this package. Morris, White and Crowther describe planning in
terms of aims, data-generating mechanisms, estimands, methods and performance
measures, with explicit Monte Carlo uncertainty. We use those distinctions in
the package's operating guidance rather than impose a fixed number of simulation
repetitions or a compulsory research sequence. [Morris et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/)

Research-agent evaluation also needs to separate producing a plausible artifact
from reproducing the required result. PaperBench supplies a relevant replication
evaluation precedent, but replicating machine-learning research does not itself
establish the correctness of statistical derivations. [PaperBench](https://arxiv.org/abs/2504.01848)
Cost, holdout construction and reproducibility are part of the comparison,
following the concerns identified by Kapoor and colleagues. [AI Agents That Matter](https://arxiv.org/abs/2407.01502)

NORA already uses scientific skills, file-backed state and separate research
evaluation in a domain-specific harness. PARNESS likewise studies research
workflow infrastructure. These are close architectural precedents, not evidence
that our statistical package improves a native host. Our comparison must therefore
test statistical research value rather than present skills or persistent files
as a new agent architecture. [NORA](https://arxiv.org/abs/2605.02092),
[PARNESS](https://arxiv.org/abs/2605.05258)

The proposed contribution is a statistical operating package and an evaluation
of its incremental value within a fixed coding host. Native skills, file-backed
work, iterative compiler feedback and separate evaluation are existing mechanisms,
not inventions claimed here. The package is useful only if it improves a measured
scientific or researcher-workflow outcome beyond a strong unmodified host.

## 2. Portable Package

The current package consists of one `SKILL.md` and two relative references.
It uses each host's supported skill activation surface. Researchers retain the
host's model, retained conversation, search, file editing and execution tools.
Installing the standalone AI-Statistician graph or a Lean environment is not
necessary to use this entry point. The package contains no model client,
credential, embedded scheduler or autonomous repair service.

The guidance is intentionally not a mathematical answer bank. It asks the author
to define the inferential question and assumptions, inspect permitted sources,
develop justified equation chains, and preserve unresolved claims. It does not
prescribe a statistical method, proof decomposition, tactic sequence or response
to a particular error. Search queries, code, derivations and every revision remain
the coding agent's decisions.

Actual mathematical content lives in ordinary files. Compact references identify
claims, dependencies and checkpoints when needed; JSON is not the authoritative
medium for a long derivation. A researcher can inspect and revise those same files
without reconstructing a nested agent transcript. Relevant paper, code and data
versions should be recorded, and reproduction should distinguish the published
environment from a subsequently adapted one.

### 2.1. Progressive Research Work

Theory does not have to finish before computation begins. Once an estimand and
an executable procedure are clear enough, a prototype can expose undefined
quantities, boundary cases or counterexamples. Exploratory computation may change
the argument. Confirmatory computation instead follows a frozen method, DGP,
metric and precision or stopping rule; its observed outcomes cannot redefine
those criteria. Failed method executions remain part of the scientific report.

Review must state its actual authority. A self-check in the author's conversation
is not an independent review. When the host provides an authorized separate
session, or a human referee is available, stable claims and exact implementation
can receive separate scrutiny. Without that channel the output remains unreviewed,
even if the author says that it is correct. The skill instructs this distinction
but cannot enforce process isolation or certify scientific truth.

### 2.2. Optional Formal Work

Lean is an additional verification route, not a mandatory exit for every research
question. Stable definitions or lemmas can be investigated early; expensive proof
work usually follows a stable statement. A formal task requires its exact target,
whereas an empirical reproduction can complete with formal work not requested.
Optional Lean does not make mathematical justification of a theoretical claim
optional; the complete informal argument still needs assessment.

The supporting EmpericalProcessLEAN repository supplies a pinned Mathlib/Statlib
project and downstream StatInference declarations. Retrieval returns candidate
premises, not proof evidence. Accessible imports, current compilation, target
identity, allowed axioms and correspondence to the informal claim are separate
checks. LeanDojo provides relevant prior work on accessible premises and verified
proof feedback; neither retrieval nor a kernel proof of a different statement
establishes source fidelity. [LeanDojo](https://arxiv.org/abs/2306.15626)

The existing library is not claimed to formalize entire textbooks. Its source
ledger contains author-maintained scope labels; these do not supply an independently
reviewed coverage denominator. Selected kernel checks and full root builds are
reported as their actual scopes. An incompatible newer library stays outside
the active proof environment until a complete migration succeeds.

## 3. Evaluation Design

### 3.1. Host Comparison and Task Population

Installation, scientific efficacy and human usability are distinct questions.
Native installation checks must demonstrate that the exact package body reaches
the model and that relative references and requested tools work. Discovery or
exit zero alone is insufficient. Version-dependent activation failures stay in
the record rather than being silently excluded.

The prospective scientific comparison is paired within an exact open-weight
host/model configuration: bare host versus the same host with the unchanged
package. Both arms receive the same scientific material, allowed sources,
environment, output contract and global resource condition. Only package
availability and its declared activation differ. Separate clean workspaces avoid
cross-arm state. All scheduled draws, including missing outputs and timeouts,
remain in the denominator; an earlier draft cannot replace a missing final result.

Published-result tasks will include replication with permitted author code,
paper-to-code work with implementation hidden, and narrowly scoped known-result
derivation. Families stay together across splits. Mathematical evaluation needs
a qualified rubric and independent authority; reference execution can judge
numerical agreement but cannot accept a derivation. Lean components have separate
exact-target outcomes. No single score will disguise incorrect theory behind
working code or optional formal failure behind correct empirical reproduction.

Task qualification precedes agent execution. A task has a specific scientific
deliverable, access condition and acceptance authority, supported by the full
source paper, relevant proof appendix, code and data. A narrow successful function
test does not qualify that paper's whole research task. Failures of the reference
analysis are resolved or declared during qualification, not removed after observing
agent performance. The selected population and exclusions determine the scope
of the eventual claim; a reproducible-source subset is not all statistical research.

Replication tasks permit author code. Paper-to-code tasks hide it and the target
numerical outputs. Known-result derivation tasks hide the target argument while
providing sufficient definitions and background. These access conditions are
reported separately, with clean runs and family-grouped splits. Recognizing a
published theorem from pretraining remains possible; hidden-source rederivation
is not evidence of discovery of a genuinely unknown theorem.

### 3.2. Scientific Assessment

The primary scientific endpoint is independently accepted full-task output for
the frozen intent. Secondary measures include derivation fidelity, implementation,
numerical agreement, empirical uncertainty, formal status, actual resource use
and operator intervention. Study size, repeats, tolerances and analysis must be
fixed before opening held results. Equal request counts are not equal tokens,
runtime or scientific computation.

Independent mathematical adjudication reads the selected derivation itself,
not its self-assessment or its similarity to a reference formula. The assessment
checks definitions, hypotheses, dependency claims and every substantive inference,
including rates, normalization and the conditions of invoked results. A changed
assumption or conclusion is recorded as such. A valid alternative argument or a
justified counterexample can satisfy a task that permits it; an incomplete argument
remains incomplete even when code and simulation agree with the expected answer.
Reviewers record the first unsupported step when identifiable and their unresolved
uncertainty. Expert identities, conflicts, blinding, adjudication and workload
must be disclosed. No qualified mathematical panel has yet been completed.

Final assessment distinguishes the scientific result from its explanation:
an accurate number, a faithful implementation, a complete argument and an honest
gap report are different observations. Automated grading, if used for mathematical
claims, must first be checked on independently adjudicated valid and invalid
artifacts; it cannot acquire authority from agreement with the author model.
PaperBench's separate JudgeEval is a relevant evaluation precedent, not a
mathematical referee for this study. [PaperBench](https://arxiv.org/abs/2504.01848)

### 3.3. Researcher Effort

A researcher-use study will separately measure setup and reproduction effort
with counterbalanced assignment and independently judged correctness where
feasible. Convenience demonstrations cannot substitute for that study. Claude
Code's separately authorized compatibility checks are not pooled with the
open-weight scientific comparison.

The effort study records installation, intervention, diagnosis and completion
time, together with whether the result is correct. A short but incorrect analysis
is not a usability success. Researchers' expertise, prior task familiarity and
training on the host/package are part of the design. Counterbalancing does not
erase carryover when a participant has already seen a task's solution; distinct
matched tasks and the exposure record are needed.

## 4. Simulation and Statistical Analysis

There are two different experimental levels. Agent draws assess the package;
datasets generated within a draw assess the statistical procedure written by
that agent. A thousand simulated datasets from one generated procedure are not
a thousand independently evaluated agent outputs. They cannot compensate for
using one paper family or one successful model draw.

For the outer comparison, the proposed estimand is the package-minus-bare-host
difference in full-task acceptance under the specified host, model, task population
and resource condition. Report family-level arm outcomes and paired differences
before any aggregate. Repeated draws estimate within-family reliability. The
number of families, task-stratum weights, draw schedule and family-level uncertainty
method must be specified before outcomes; variants and rubric fields are not
independent samples. With only a purposively selected case or very few families,
report descriptive evidence rather than a general-population efficacy estimate.
Neither size nor precision has yet been fixed for the official study.

Within a statistical-method task, the generated experiment must describe its aim,
DGP, estimand, methods and performance measures. Comparators must address the same
estimand and use appropriate, documented settings. Scenarios should examine the
conditions on which the argument depends, relevant finite-sample behavior and
scientifically meaningful departures, not just settings favorable to the proposal.
Monte Carlo uncertainty accompanies bias, error, coverage, power or other specified
measures. Where justified, methods use the same generated datasets for paired
comparison. Failure rates and performance conditional on valid outputs are
reported separately. [Morris et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/)

Numerical reference checks qualify an implementation comparison within their
scope. Diagnostic simulations may expose contradictions; finite numerical
agreement does not prove identification, consistency, a central limit theorem
or a universal inequality. Confirmatory repetitions are chosen for the specified
Monte Carlo precision, not a fixed count or a desired significance result.
The reference, tolerances, handling of numerical failures and any valid stopping
rule are fixed before assessment. Mechanism unit tests are not this simulation
study, and operator-run reference scripts are not autonomous agent outcomes.

All scheduled agent draws remain in the outer denominator. Missing final outputs,
execution failures and timeouts are reported by cause, with complete observed
resource use; unknown usage is not zero. Setup and reference-qualification costs
are reported separately from agent execution and expert grading. Matched scientific
access and measured resources, not equal request caps alone, support attribution.

## 5. Scientific Case Study

The application must demonstrate a consequential statistical task, not just skill
activation or a working script. Selection will be made before outcomes, based on
an explicit question, accessible data and source rights, a relevant methodological
difficulty, a credible comparator and an independently assessable result. The
case will state the population, outcome, estimand, assumptions and interpretation,
then connect the argument to the executed method and its diagnostic or sensitivity
analysis. A published-method reproduction is labelled as reproduction rather than
novel theory. No qualifying case has yet been completed for this paper.

The case report will show the actual package and bare-host deliverables, the
decisions that matter scientifically, errors or unresolved conditions, and human
interventions. A retrospective success vignette can illustrate behavior but cannot
estimate efficacy. Selection among ideas, runs or manuscripts must be disclosed.
AI Scientist-v2 explicitly separates autonomous work within a run from human
selection of ideas and completed manuscripts; its selected-paper result is not
a population success rate. [AI Scientist-v2](https://arxiv.org/abs/2504.08066)

The main paper will contain the scientific interpretation and essential results;
the supplement will contain the complete derivation, exact source, execution
logs and additional diagnostics. A missing result is not replaced by a plausible
narrative. Both successful and unsuccessful prespecified cases are retained.

## 6. Evidence and Remaining Work

The [installation record](../docs/portable_harness_installation.md) separates
native Codex discovery, Qwen/Kimi activation observations and Claude Code body
uptake. These establish different compatibility scopes, not cross-host efficacy.
Consumed Qwen development failures remain outside the main test pool. Historical
Haiku records are development archives only, not publication baselines.

No official comparative result or human usability estimate is available. Before
submission, the study needs qualified fresh tasks, fixed resource conditions,
independent adjudication, complete outcomes and uncertainty estimates. The release
also needs original-code licensing and third-party source rights resolved. No
result table, superiority statement or autonomous-discovery claim is warranted
until those obligations are met.

The current package is research guidance, not an enforcing tool layer. Its
mechanisms largely reuse the host. A software contribution will require a useful,
documented release and a clear advantage over existing guidance, or the claim must
be narrowed. An architecture description alone does not supply that advantage,
and a new statistical theorem is not manufactured to make the software appear
methodological. The appropriate venue depends on the demonstrated contribution.

## Appendix A. Mathematical and Experimental Materials

The supplement will contain each assessed task's definitions, assumptions,
theorem or claim, complete proof and reference dependencies. Derivations use
reviewable Markdown/LaTeX and vertical equation chains with one justified change
per line where a calculation is involved. Exact identities, implications,
inequalities, approximations and limits use their respective symbols. No fixed
number of steps or a filled schema establishes correctness. Counterexamples,
conditional conclusions and unresolved proof obligations retain their actual
status. Numeric diagnostics are separately identified and do not replace a proof.

Task materials will state what the agent could see and what was held by the
evaluator. Hidden mathematical gold includes admissible alternative arguments,
scope-changing errors and expert assessment instructions, not just one target
formula. The study record will preserve source versions, task exclusions and the
expert qualification process. Full DGPs, method settings, random-number handling,
precision choices, failures and result-generation scripts support the reported
simulation results.

## Appendix B. Host and Release Reproduction

The release record will supply the exact package and host versions, installation
and activation instructions, relative-reference checks, allowed tools, model
weights/runtime/template, sampling, context and stopping settings. Complete
scheduled-draw accounting and actual final artifact references will support the
main comparisons. Native host differences and operator interventions are disclosed;
compatibility-only observations remain separate from scientific outcomes.

All paper and supplement tables and figures need documented reproduction paths
from released, licensed inputs. JSS specifically asks for code and replication
materials supporting reported results; MLOSS emphasizes usable, documented
nontrivial software. Those are distinct venue requirements, not proof that this
package qualifies for either. Rights, installation and independent assessment
remain unresolved. [JSS author information](https://www.jstatsoft.org/authors),
[MLOSS criteria](https://jmlr.org/mloss/mloss-info.html)

## Appendix C. Optional Lean Scope

The library report will list curated informal targets, source locations, exact
Lean declarations, active imports and dependencies, compiled-project pins and
axiom audits. Statement correspondence is assessed separately from compilation.
Coverage requires an explicitly defined source inventory and reviewed mapping;
file/declaration counts cannot stand in for a denominator. Library construction
and human contributions are not autonomous agent proof outcomes. Appendix C
will share the foundation provenance with the companion system paper without
presenting it as a second independent library experiment.

## Reproducibility Sources

The implementation and current operating contract are in
[AI-Statistician](https://github.com/ykzeng-yale/AI-Statistician); the shared Lean
foundation is in [EmpericalProcessLEAN](https://github.com/ykzeng-yale/EmpericalProcessLEAN).
The [experiment specification](../docs/publication_experiments.md) is a design
record, not an activated preregistration. Permitted artifacts, exact versions,
failures and adaptations will accompany the completed study. Private credentials,
private model reasoning and source assets without redistribution rights will
not be included in a public release.
