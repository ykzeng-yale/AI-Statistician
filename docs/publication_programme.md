# Publication Programme

Updated: 2026-10-02. Status: design and release work in progress; no new scientific
benchmark result. The native chat goal is active and covers both publications.

## Two Research Questions

**Paper H: A Portable Harness for Reviewable Statistical Research.** Can a small,
host-independent research workspace and evidence/tool layer improve the
correctness, reproducibility and usability of statisticians' existing coding
agents? Researchers keep their host agent and model. Theory lives in
Markdown/LaTeX; computation uses local Python/R; Lean is selected by task intent.
The deliverable is an installable skill/tool package, reference workspaces and
reproducible host conformance, followed by scientific and researcher-use studies.
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
| Portable host | Native host file/edit/search/execution tools and Agent Skills format | Clean installation, host discovery, tool access and real researcher usability |
| Retained research session | `client_tool_loop.py`, hash-bound files and raw observations | Local Qwen conformance for every workspace and long-session recovery |
| Collaboration | `agent_runtime.py`, scoped roles and reference handoffs | Dependency-aware independent work, exact-input joins and evidence invalidation; current execution is serial/interleaved |
| Scientific execution | Existing local Python/R tools and project snapshots | Native environment reconstruction and Python/R reproduction on clean machines |
| Verification | Independent review, frozen confirmation and exact Lean checks | Qualified independent Qwen-era evaluation plus expert calibration |
| Lean foundation | Pinned Mathlib/Statlib/StatInference and retrieval | Audited statement/proof/dependency maps and a compact curated public API |

Extend the sole runtime if independent scheduling is justified; do not layer a
second framework over it. Model authors all derivations and code revisions. The
harness supplies tool state, execution, source identity, permissions and evidence
authority. Do not add theorem-family logic, grammar repairs or generated-answer
patches. A demonstration of a model error is not by itself a harness defect.

## Current Audit Evidence

Inspected commits: AI-Statistician `4c0a1ade`, EmpericalProcessLEAN `4cec7860c`.
Both were clean and their remotes were fetched. This audit inspected canonical
entry points, session/provider contracts, installation metadata, source maps,
Lean tooling and branch ancestry; it is not a claim that every source line or
external paper has received expert review.

- The full `StatInference` root built locally on Lean 4.30.0 (9843 Lake jobs,
  including cached replay). This is not a clean-machine or all-declaration axiom
  audit; the root file has zero declarations to scan.
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

## Delivery Order And Manuscripts

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

1. Finish the scientific argument in each existing manuscript master: question,
   contribution relative to the closest work, actual intervention, baselines,
   mathematical authority, simulation design, case and complete supplement.
   Current expanded methods are prospective; no results have been supplied.
2. Qualify the study's paper families and case from their full papers, relevant
   proof appendices, code and data. Review assumptions and the argument separately
   from reference execution. Preselect cases by scientific purpose, not observed
   agent success. Set scope, exclusions, endpoints, sample/precision rationale
   and family-level analysis; do not keep replacing failed families with easy ones.
3. Resolve actual arm/tool/source/confirmation/resource comparability. Test only
   demonstrated mechanism blockers with deterministic fixtures first. Native
   Qwen/host conformance, installation and a compact source-faithful Lean release
   support these deliverables; they are not parallel open-ended side projects.
4. Freeze and run fresh open-weight studies, collecting all scheduled outcomes,
   resource use and interventions. Obtain independent scientific adjudication.
   Existing consumed evaluations remain immutable development records. A source-only
   reproduction does not measure specialist collaboration; inner Monte Carlo
   repetitions do not increase the outer agent sample.
5. Complete the results and substantive case accounts in both masters, with full
   mathematical arguments and reproducible main/supplement tables and figures.
   Report negative outcomes and uncertainty without changing the original claims.
6. Finish clean installation and licensing/attribution, with a defined Lean
   coverage inventory rather than declaration counts. Deposit each arXiv paper
   only when its own release and scientific evidence support its contribution.

Likely venue fit is a later decision: a useful statistical software/research
workflow contribution can fit a computational-statistics/software venue; a
controlled agent architecture/benchmark contribution can fit an AI venue.
Publication in a theory journal would require substantive statistical theory,
not a software system renamed as a method. Acceptance is never assumed.

See [current sources and adoption decisions](publication_sources_20261001.md)
for dated primary papers, inspected code pins and license boundaries.
