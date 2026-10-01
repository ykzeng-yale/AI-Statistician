---
name: statistical-research
description: Develop or reproduce statistical methods research with reviewable mathematical derivations, local Python/R experiments, and optional Lean verification. Use for a research idea or published method, not routine data summaries or a request to repair the harness itself.
---

# Statistical Research

Use the host coding agent's own file, search and execution tools. There is no
embedded model client or second scheduler. Read only the project context and
references needed for the current question. See
[research workspaces](references/workspaces.md) for scientific artifacts and
[local tooling](references/tooling.md) when using the AI-Statistician checkout.

Clarify the inferential question, permitted sources and required evidence.
Distinguish identification, estimation and inference. Investigate reusable
literature/code when permitted, pin the selected sources, and reproduce relevant
baselines before interpreting a new improvement. Blind tasks retain their source
restrictions; target papers, hidden implementations and judge outputs are not
research context.

Maintain substantive mathematics in Markdown/LaTeX files. State definitions and
assumptions explicitly; develop justified equation chains and dependent claims,
with counterexamples, conditional results and unresolved gaps kept visible.
Choose useful derivation length and local edits yourself. JSON can identify
artifacts but is not the mathematical research medium.

Prototype when the estimand and computational interface are sufficiently clear.
Use exploratory Python/R to challenge claims and inform the next derivation.
Read raw errors/results and author your own revisions in the same workspace;
do not introduce issue-specific correction scripts or statistical answer rules.

Seek independent mathematical and exact-code review of stable claims when the
host offers an authorized independent session or an external referee. Keep the
author separate from the reviewer. Without independent review, report an
unreviewed result rather than manufacture acceptance through self-agreement.
Review findings should cite exact files and assumptions; source owners revise.

Freeze confirmatory DGPs, methods, metrics and Monte Carlo precision/stopping
before outcomes. Distinguish diagnostic simulation from confirmation, preserve
method failures and report uncertainty. Choose a scientifically appropriate
repetition count rather than a universal fixed number.

Formalization follows task intent. Stable definitions/lemmas may be investigated
early; expensive proof usually follows stable statements. Reuse the pinned
Statlib/Mathlib foundation and accessible declarations. Iterate on model-authored
Lean using real compiler/goal feedback. Exact target identity, source fidelity and
an axiom-clean active-project check are separate requirements for proof evidence.
An optional formal gap does not erase valid non-formal results.

Deliver reviewable claims, exact code, reproducible execution, source provenance,
empirical uncertainty and honest gaps. Separate reproduced, independently reviewed,
empirically supported and kernel-closed evidence. Host skill instructions do not
enforce runtime isolation or certify a scientific result; describe actual tool
permissions and review authority in the report.
