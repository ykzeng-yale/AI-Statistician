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

The primary scientific endpoint is independently accepted full-task output for
the frozen intent. Secondary measures include derivation fidelity, implementation,
numerical agreement, empirical uncertainty, formal status, actual resource use
and operator intervention. Study size, repeats, tolerances and analysis must be
fixed before opening held results. Equal request counts are not equal tokens,
runtime or scientific computation.

A researcher-use study will separately measure setup and reproduction effort
with counterbalanced assignment and independently judged correctness where
feasible. Convenience demonstrations cannot substitute for that study. Claude
Code's separately authorized compatibility checks are not pooled with the
open-weight scientific comparison.

## 4. Evidence and Remaining Work

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

## Reproducibility Sources

The implementation and current operating contract are in
[AI-Statistician](https://github.com/ykzeng-yale/AI-Statistician); the shared Lean
foundation is in [EmpericalProcessLEAN](https://github.com/ykzeng-yale/EmpericalProcessLEAN).
The [experiment specification](../docs/publication_experiments.md) is a design
record, not an activated preregistration. Permitted artifacts, exact versions,
failures and adaptations will accompany the completed study. Private credentials,
private model reasoning and source assets without redistribution rights will
not be included in a public release.
