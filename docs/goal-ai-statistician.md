# AI Statistician Objective

Build a fully autonomous AI Statistical Theory Lab in this repository. It should
ingest fresh JASA/AOAS/frontier-style questions or papers, develop rigorous new
statistical theory, implement and stress-test methods in Python and R, formalize
exact theorem targets in Lean, reuse the strongest available formal libraries and
RAG infrastructure, learn from execution/proof traces, and report evidence and
remaining gaps honestly.

## Generalization Invariants

1. Core runtime and prompts are domain-neutral. A named statistical family may
   appear in benchmark data or retrieved source, never as a runtime branch.
2. The LLM owns theory and complete Python/R/Lean source. The harness returns raw
   environment observations and never writes a content patch.
3. Local compiler, simulation, and ABI failures return to the same source-owning
   model. Architect handles only cross-workspace planning or exhausted budgets.
4. Candidate generation and acceptance are independent. A source agent cannot
   weaken its own gate or promote its own proof.
5. Confirmatory empirical authority is frozen before results. A failed candidate
   cannot revise its own threshold and reuse the same observations.
6. Formal RAG reuses Mathlib, Statlib/StatInference,
   `lean-stat-learning-theory`, `EmpericalProcessLEAN`, OpenProver, and
   CodexProver conventions and declarations. Retrieved content is context, not
   proof, until checked in the active project.
7. Independent reviewers report findings but do not choose repair owners or
   routes. The source model revises locally; Architect routes globally.
8. Only exact target-bound Lean kernel promotion proves the requested theorem.
   Compiled helpers and weakened targets remain scoped candidate evidence.
9. Tests and evaluations use exactly `claude-haiku-4-5-20251001`; production may
   use Haiku or Sonnet, never Opus.
10. Development uses multiple unrelated families. Held-out tasks remain sealed
    and cannot be used to create vocabulary, theorem, metric, or Lean rules.

## Task-Intent Completion Contract

Every evaluated task freezes its evidence requirements before the first product
model call. The same run must satisfy every dimension marked `required`, disclose
the status of every `advisory` dimension, and must not invent work for a dimension
marked `not_applicable`:

- source replication: pinned source, code, data, environment, and result comparison;
- theory: fresh artifact-backed Markdown/LaTeX derivation plus independent review;
- scientific code: model-authored Python/R source, isolated execution, and
  independent semantic acceptance;
- empirical: a pre-result frozen protocol and fresh confirmatory measurements;
- formal: exact Lean statement, task-bound retrieval, live Lean feedback,
  independent statement-faithfulness acceptance, and exact kernel closure;
- novelty: frozen source horizon and an evidence-backed novelty assessment;
- unresolved gaps: final Critic disclosure without converting absence of evidence
  into acceptance.

Formalization is a product capability, not a universal completion bottleneck. It is
mandatory for formal/proof tasks and formal-library benchmarks, advisory when the
task asks for an optional correctness audit, and nonblocking when frozen intent
marks it not applicable. A formal failure cannot erase independently valid theory or
empirical evidence, but it must remain visible in the evidence vector.

Held-out evaluation begins only after the corresponding development tasks close at
their frozen intent. Separate formal integration milestones require exact kernel
closure on multiple unrelated formal tasks. Neither milestone alone establishes
complete product readiness: broader paper ingestion, theory depth, replication,
scientific computing, library growth, and cross-task learning still need evidence.

## Current Status

The evidence boundary, direct Python/R source loop, direct Lean source loop,
content-addressed lineage, and single runtime endpoint are implemented and covered
by deterministic tests. The old repair/bridge/planner side systems have been
removed from the canonical package.

The current measured capability and immutable consumed-task record live in
[`main_worker_status.json`](main_worker_status.json). Passing deterministic harness
tests or one evidence dimension is never promoted to full-task capability. The
system must not be described as fully end to end until fresh cross-family tasks close
under their frozen intent.

The machine-readable frozen split is
[`benchmarks/autonomous_cross_family_e2e_protocol_20260713.json`](../benchmarks/autonomous_cross_family_e2e_protocol_20260713.json).
The active architecture is [production_design.md](production_design.md).
