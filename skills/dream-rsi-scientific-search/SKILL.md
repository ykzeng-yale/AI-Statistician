---
name: dream-rsi-scientific-search
description: Use measured experiment histories to plan or improve executable scientific candidate search, including Dream-RSI adoption and exploration-policy evaluation. Use for choosing between refinement and new research directions, not routine bug fixes, ordinary statistical analysis, or mathematical certification.
---

# Evidence-Grounded Scientific Search

This is an instruction-only, Dream-RSI-inspired skill, not the upstream harness
or an implemented replay simulator. Use existing tools and research workspaces.
For source pins, paper limitations, or AI-Statistician integration, read
[the adoption analysis](references/adoption.md). Do not require replay or a search
tree for a task that can be handled directly.

## Keep Research and Search Control Separate

Establish what the user wants improved: a scientific candidate, or the system
that produces candidates. When improving AI-Statistician, the product model must
author its derivations and programs. Operator-written answers or repaired
benchmark outputs are not product capability.

Keep task correctness separate from the quantity being optimized. Executable
scores can compare valid implementations or numerical constructions. They cannot
establish statistical assumptions, theorem truth, or faithfulness of a Lean
statement. Keep theory in reviewable Markdown/LaTeX and retain independent review;
formalization remains optional unless task intent requires it.

## Use History to Choose Useful New Work

Read relevant prior candidates and their actual observations on demand. Reuse
existing artifact references, source hashes, parent checkpoints, evaluator and
environment identities. Do not create another history database or require every
old proposal in every context window.

Choose whether to refine a promising candidate, investigate a failure, try a
different mechanism, or finish. Base the choice on observed evidence and the
scientific objective, not branch IDs, fixed widths, retry quotas, or a required
error taxonomy. An implementation failure alone does not settle the underlying
research idea; inspect its source and raw observation before drawing that
conclusion. The same source-owning model authors any revision.

Use the existing local Python/R/Lean execution tools for new, permitted work.
Do not introduce a VM, remote service, new scheduler, or extra agent merely to
use this skill. Independent candidate work can run concurrently only when the
host already supports isolated state and the task authorizes it. Otherwise use
the existing serial loop; do not report hypothetical parallelism as saved time.

Record the candidate's mechanism and unresolved assumptions with references to
its measured results. Distinguish a proposed improvement from an executed one.
Let the evidence determine useful effort; do not stop solely to reduce calls,
force another iteration, or replace a failed benchmark with an easier one.

## Replay Is a Separate, Conditional Experiment

Only consider offline policy comparison when an actual replay implementation and
explicitly designated exploratory training histories are available. Absence of
either is a reported limitation, not an instruction to build infrastructure.
Consumed evaluations, sealed gold, and confirmatory outcomes are not tuning
data. Never reopen, repair, rescore, or promote them through replay.

A replay decision may inspect only the observations available at that point.
Reset policy state between histories. Keep hidden future results and outcome-
derived metadata outside its inputs; reject a requested continuation without a
recorded matching context as unsupported. A branch whose generation depended on
other branches cannot simply retain its old outcome after those dependencies
are removed or reordered. Do not synthesize missing scores or call the research
model/evaluator to fill holes while calling the result offline replay.

Keep recorded outcomes unchanged. A new search-policy statistic is not a new
scientific evaluation, proof, or unbiased estimate of future performance.
Changes to the generator, prompt, tools, evaluator, or environment need fresh
prospectively defined validation, not inherited replay credit.

## Report the Right Result

Report the best *valid* artifact, remaining scientific gaps, why the next
direction is worth trying, and whether each observation is live or recorded.
For policy comparisons, separate policy-development cost, discovery-model cost,
execution/review cost, and actual wall time. Count failed attempts too.
Use disjoint future tasks to test transfer, keeping the generator and evaluator
fixed for the comparison. Replay improvement alone is not a capability claim.

In AI-Statistician, preserve the sole `AgentRuntime`, shared retained tool loop,
frozen evidence boundaries, and exact test model `claude-haiku-4-5-20251001`.
This skill does not install itself into the product's Anthropic prompts or
authorize an additional live evaluation.
