# AI Statistician Multi-Codex Blueprint

This repository is building a live AI Statistical Theory Lab, not a static
benchmark harness. Multiple Codex workers should use this document as the
shared operating contract.

Main-worker ownership and the current compact handoff live in
`docs/main_worker_ownership.md` and `docs/main_worker_status.json`.

## Core Goal

Build a Claude/OpenAI-generator-backed agent runtime that can:

1. Ingest open statistical research questions or papers.
2. Let an Architect choose the research path and evidence contract.
3. Let LLM TheoryDeveloper propose estimands, procedures, assumptions,
   theorem statements, derivation DAGs, and failure risks.
4. Let LLM SimulationEngineer and AlgorithmEngineer write code, run it
   locally, inspect stdout/stderr/results, revise, and rerun.
5. Let LLM Formalizer and ProofEngineer generate Lean candidates, receive
   real Lean/AXLE/prover diagnostics, repair candidates, and rerun checks.
6. Let CriticEvaluator distinguish supported claims, falsified claims, open
   formal gaps, and next actions.
7. Persist runtime learning rows so future runs improve from simulation,
   implementation, proof, and critique traces.

Validators are gates, not the main intelligence. Lean/AXLE evidence is only
proof evidence after kernel verification.

## Non-Negotiable Capability Boundaries

The following can test plumbing, but must not be counted as agentic capability:

- static/replay providers
- deterministic TheoryDeveloper/Formalizer fallbacks
- registered algorithm templates
- registered simulators
- proof-bank rows without local kernel evidence
- retrieval hits, route adoption, queue creation, or audit success alone
- deterministic theorem-closure work-order seeds

Capability claims require live Claude/OpenAI generator evidence plus local
environment execution or verifier feedback. In particular:

- Algorithm capability requires generated algorithm code, local execution,
  captured output/error, and preferably a fail-then-pass repair sequence.
- Simulation capability requires generated DGP/stress-test code, local
  execution, captured metrics/output/error, and preferably repair.
- Formalizer/ProofEngineer capability requires a live LLM proposal, materialized
  Lean candidate, local Lean/AXLE diagnostics, proof-state feedback to the LLM,
  and a repair attempt. Deterministic closure packets are work orders only.
- Full theorem proof requires local Lean/AXLE/kernel verification of the source
  theorem or explicitly required subclaims, with no hidden sorry/axiom/admit.

## Formal Verification Policy

Each run should carry an evidence contract:

- `required`: final acceptance requires formal proof closure.
- `optional`: Architect chooses simulation-first, proof-first, or dual-track,
  and reports any formal gaps.
- `advisory`: formalization is used for diagnostics only; final output may rely
  on derivation, implementation, simulation, and critic review, but must disclose
  that it is not formally verified.

Do not use a single ambiguous `ACCEPTED` status as theorem proof. Prefer
explicit states such as runtime completed, simulation supported, formal
subclaims verified, full theorem kernel verified, or formal required blocked.

## Parallel Work Rules

Parallel Codex workers should pick one narrow lane and avoid broad audits unless
the lane explicitly requires them.

Recommended lanes:

- `architect-runtime`: improve Architect path planning, evidence contracts, and
  live reroute policy.
- `theory-simulation-algorithm`: improve live TheoryDeveloper, SimulationEngineer,
  AlgorithmEngineer code generation, local execution, and repair evaluations.
- `formalizer-proofengineer`: improve live Lean candidate materialization,
  ProofEngineer diagnostic feedback, Lean LSP/MCP or prover adapter calls, and
  repair loops.
- `proof-library`: add reusable Lean/statistics proof kernels with local kernel
  manifests.
- `cross-task-eval`: add non-conformal tasks such as randomization variance,
  FDR, KKT/certificate, or empirical-process bounds.

Before changing code, inspect current git status and the latest runtime manifest.
After changing code, run focused tests and push the active coordination branch.
For RAG and Lean source-control scope, use
`docs/rag_lean_source_control_inventory.md`; it distinguishes committed source
from intentionally untracked generated indexes, run artifacts, and Lean build
outputs.

## Current Architectural Priority

Do not expand broad audit/planner layers unless necessary to protect evidence
truth. The current priority is to make the live agent runtime stronger:

1. Architect decides the research path.
2. LLM workers generate theory/code/Lean.
3. Runtime executes locally and captures output.
4. Failures route back to the responsible LLM worker.
5. Validators decide what evidence is admissible.
6. Memory rows guide the next iteration.

The system should become a genuine agentic research environment, not a Codex
operator manually debugging each subsystem.
