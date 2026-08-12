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

## Completion Contract

For each evaluated task, the same run must contain:

- a fresh plan and artifact-backed theory derivation;
- model-authored scientific source and isolated execution;
- independent semantic acceptance;
- a pre-result frozen simulation protocol and fresh measurements;
- an exact Lean statement and complete model-authored source;
- task-bound retrieval and live Lean feedback used by the prover model;
- independent statement-faithfulness acceptance;
- exact source-theorem kernel closure;
- final critic acceptance with no hidden formal gap.

Two development families must close before held-out evaluation begins. That is an
integration milestone, not complete product readiness: broader arbitrary-paper
ingestion, theory depth, library growth, and cross-task policy learning must also
be demonstrated.

## Current Status

The evidence boundary, direct Python/R source loop, direct Lean source loop,
content-addressed lineage, and single runtime endpoint are implemented and covered
by deterministic tests. The old repair/bridge/planner side systems have been
removed from the canonical package.

The latest authoritative live development panel, v387, scored 7/16 and still has
0/2 exact theorem closures. It verified fresh post-outcome cohort independence and
reached real Algorithm, Simulation, review, theory revision, RAG, and one Formalizer
attempt. It also exposed a shared source-ownership bug: after eight direct Haiku
Simulation submissions still violated literal frozen metric paths, runtime treated
successful process execution as source validity, sent the failed artifact to review,
and allowed Architect to rename a Simulation rewrite as AlgorithmEngineer work.
Commit `f7a8538f` makes the direct workspace and downstream gate use one outcome-blind
source-validity predicate, preserves immutable source identity, and clarifies mutable
source versus contradictory parent semantics. An exact-Haiku replay of the frozen
v387 review now selects source-only revision under `SimulationEvaluator`; this is
diagnostic replay evidence, not integrated capability credit. No repair agent,
content patch, or task-family rule was added. The system must not yet be described
as fully end to end.

The machine-readable frozen split is
[`benchmarks/autonomous_cross_family_e2e_protocol_20260713.json`](../benchmarks/autonomous_cross_family_e2e_protocol_20260713.json).
The active architecture is [production_design.md](production_design.md).
