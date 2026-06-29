# Multi-Codex Coordination Blueprint

Updated: 2026-06-29

This document is the handoff contract for multiple Codex sessions working on
AI Statistician at the same time. It is intentionally operational: future
workers should read it before making architectural changes.

The main-worker ownership contract is
[`docs/main_worker_ownership.md`](main_worker_ownership.md). The compact
machine-readable status handoff is
[`docs/main_worker_status.json`](main_worker_status.json).

## Shared Branch Policy

Use a shared coordination branch for the current consolidated worktree:

```text
codex/ai-stat-lab-sync-20260625
```

Do not start new work from a stale local `main` checkout. At the time this
blueprint was written, local `main` was behind `origin/main` and the local
workspace contained substantial uncommitted runtime/proof/capability changes.
The shared branch is the place where those changes are published for parallel
Codex work.

Recommended flow for future sessions:

1. Fetch the repo.
2. Check out `codex/ai-stat-lab-sync-20260625`.
3. Create a focused child branch from it, for example
   `codex/proofengineer-lsp-loop` or `codex/architect-path-policy`.
4. Keep commits small and tied to a capability seam.
5. Open a PR back to the coordination branch or to `main` only when the merge
   target is explicit.

Never force-push `main` from a dirty or behind checkout.

## Canonical Goal

The product target is a fully autonomous AI Statistical Theory Lab:

```text
Open statistical question / paper
  -> Architect-controlled AgentRuntime
  -> TheoryDeveloper derives estimands, procedures, theorem candidates
  -> AlgorithmEngineer writes/runs/repairs local code
  -> SimulationEngineer writes/runs/repairs DGP stress tests
  -> Formalizer/ProofEngineer authors Lean candidates and consumes verifier feedback
  -> RAG/SearchMemory retrieves papers, Lean/Mathlib/StatInference/OpenProver knowledge
  -> CriticEvaluator audits theory, code, simulations, and proof gaps
  -> EvidenceLedger records what is proposed, simulated, kernel-verified, or open
  -> AgentRuntime reroutes based on actual tool observations
```

The system must not collapse into a static benchmark runner, a deterministic
template router, a release/audit bundle, or a Lean-only prover wrapper.

## Evidence Boundaries

These are hard boundaries for progress claims:

- Live Claude/OpenAI generator output is proposal evidence, not proof evidence.
- Retrieval hits are grounding/search evidence, not proof evidence.
- Simulation and code execution are empirical/software evidence, not theorem
  proof.
- Static/replay/template-only paths are plumbing tests only. They cannot count
  as agentic capability.
- Local Lean/AXLE kernel verification of the intended formal claim is the only
  proof evidence.
- Lean LSP MCP, OpenProver, ReProver, LeanDojo, search, diagnostics, and
  `lean_goal` output are proof-state/search observations. They guide
  ProofEngineer, but do not prove the theorem.
- Registered helper lemmas and bridge closures are proof evidence only for
  those helper claims. They do not prove the source theorem unless the exact
  source theorem is kernel-verified.
- Route-critical proof/formal agenda rows and bounded pending-task runtime
  memory must carry explicit `target_ids`; targetless rows are orchestration
  context only and should not steer source-theorem repair.
- Explicit subsystem handoff artifact ids must resolve to the requested
  artifact kind or route back to the producer subsystem. Falling back to the
  latest blackboard artifact is not end-to-end handoff evidence.

## Capability Ladder

Use this ladder when reporting progress:

```text
L0 schema/static replay passes
L1 live generator packet valid
L2 live Architect-controlled runtime completes
L3 generated algorithm/simulation code executes locally
L4 generated code fails, returns stderr/stdout, and is repaired by the LLM agent
L5 Formalizer emits materialized Lean candidate and local Lean checks it
L6 ProofEngineer receives real verifier/proof-state tool traces and repairs
L7 helper/bridge subclaims are kernel verified
L8 full source theorem is kernel verified
L9 cross-task generalization across multiple statistics problem families
```

Do not call the system "done" unless the relevant level is explicitly reached
by current evidence.

## Current Known State

The live runtime has moved beyond static scaffold:

- Anthropic/Claude generator routing is active in recent live runs.
- Cost-tier split is intended to be Sonnet for Architect/Theory/Formalizer and
  Haiku for Simulation/Algorithm/Critic.
- Generated algorithm code and generated simulation code have executed locally
  in capability runs, including failed-then-passed repair sequences.
- Formalizer Lean candidates have been materialized and checked locally.
- The latest combined runtime lineage records generated AlgorithmEngineer
  repair, generated SimulationEngineer repair, and Formalizer Lean candidate
  repair in the same resumed history.
- Proof-state feedback rows now preserve `executed_tools` and
  `tool_call_trace`.
- An opt-in Lean LSP MCP provider exists for materialized Formalizer
  candidates through `--formalizer-candidate-lean-lsp-mcp`.
- Runtime audit scorecards now include explicit-handoff and route-critical
  target-identity gates. A live run can have useful Lean/code evidence and
  still fail readiness if current pending memory or agenda rows lose their
  artifact or theorem target identity.

The system is still incomplete:

- `split_conformal_coverage` source theorem is not kernel verified.
- Recent live conformal runs still stall in Formalizer/Critic repair with open
  formal gaps.
- Dominant Formalizer failure mode: replacing a probability/coverage source
  theorem with a diagnostic helper theorem. Compiled helper candidates are
  explicitly not source-theorem proof evidence.
- Premise-derivation bridge rows are mostly not evidence-eligible or not kernel
  verified.
- Cross-task capability beyond conformal has not been proven.
- Some broad formalization-gap/audit infrastructure is useful telemetry but
  should not dominate the core AgentRuntime path.

## Current Priority Seams

Parallel Codex sessions should choose one seam and avoid cross-cutting churn.

### Architect / Research Path Planner

Goal: make Architect select `simulation_first`, `proof_first`, or `dual_track`
based on problem type and evidence policy.

Acceptance evidence:

- Live Architect-enabled run.
- The path decision is recorded in runtime artifacts.
- Static/no-Architect runs do not satisfy capability evidence.

### TheoryDeveloper

Goal: make TheoryDeveloper output step-by-step statistical derivation DAGs:
assumptions, estimand, procedure, theorem candidates, proof route, simulation
predictions, and formalization obligations.

Acceptance evidence:

- Live Claude/OpenAI TheoryDeveloper packet.
- Critic can route a concrete derivation flaw back to TheoryDeveloper.
- Simulation or formal proof feedback changes the next theory packet.

### AlgorithmEngineer / SimulationEngineer

Goal: preserve the LLM-powered coding-agent loop:

```text
Claude proposes code
  -> runtime writes sandbox artifact
  -> local Python executes
  -> stdout/stderr/result.json are captured
  -> Claude receives failure feedback
  -> repaired code executes
```

Acceptance evidence:

- `n_generated_code_sandbox_executed > 0`
- `n_generated_simulation_sandbox_executed > 0`
- failed-then-passed repair rows are attached to the live task, not just
  aggregate history.

### Formalizer / ProofEngineer

Goal: turn Lean/prover failures into internal agent repair loops:

```text
Formalizer emits Lean candidate
  -> runtime materializes exact `.lean` artifact
  -> local Lean/AXLE runs
  -> Lean LSP MCP / search tools provide goal diagnostics when enabled
  -> Claude ProofEngineer receives executed tool traces
  -> Claude repairs candidate or splits lemmas
  -> runtime reruns local Lean/AXLE
```

Acceptance evidence:

- Local Lean tool call is recorded in `executed_tools`.
- Lean LSP MCP live calls are counted only when a real MCP tool call returns a
  tool-level result or timeout. Session startup failures must not count.
- Repaired candidate preserves the source theorem shape or explicitly routes
  helpers as support lemmas/formal gaps.
- Kernel proof is claimed only when the intended claim is verified.

### RAG / Lean / OpenProver Search

Goal: use retrieval to help the agent work, not as a substitute for proof.

Acceptance evidence:

- Runtime records which DB/index/tool was used.
- Search hits are fed into TheoryDeveloper/Formalizer/ProofEngineer context.
- No report claims LeanDojo/ReProver/OpenProver extraction unless there is an
  artifact path and validation manifest.

## Formal Verification Policy

Tasks should carry a formal-verification policy:

- `required`: final acceptance requires local Lean/AXLE proof of required
  theorem/subclaims.
- `optional`: Architect decides whether simulation-first, proof-first, or
  dual-track is most efficient; formal gaps must be disclosed.
- `advisory`: formal tools are used for diagnostics and subclaim sanity, but
  simulation/code/critic evidence can support an early research candidate.

Avoid a generic `ACCEPTED` status without qualifiers. Prefer explicit statuses
such as:

- `RUNTIME_COMPLETED_WITH_FORMAL_GAPS`
- `SIMULATION_SUPPORTED_NOT_PROVED`
- `HELPER_SUBCLAIMS_KERNEL_VERIFIED`
- `SOURCE_THEOREM_KERNEL_VERIFIED`
- `FORMAL_REQUIRED_BLOCKED`

## Validation Commands

Use focused tests before broad audits:

```bash
.venv/bin/python -m pytest -q tests/test_research_agent_runtime.py -k \
  'coding_agent_capability or formalizer_lean_candidate or proof_state_provider'

.venv/bin/python -m py_compile \
  ai_statistician/proof_state_feedback.py \
  ai_statistician/research_agent_runtime.py \
  ai_statistician/cli.py \
  tests/test_research_agent_runtime.py

git diff --check
```

For Lean evidence, cite the exact manifest path and counts. Do not summarize a
mock/static proof row as kernel proof.

## Worktree Hygiene

- Prefer small branches and PRs.
- Do not silently revert files touched by another Codex session.
- Do not stage `.env` or raw secrets.
- Run a secret scan before publishing broad worktree commits.
- Do not commit `runs/` artifacts unless a specific, small, reviewable manifest
  is part of a benchmark/evidence PR.
- Do not run broad research-system audits unless the latest runtime evidence is
  missing or stale.

## Immediate Blockers To Pick Up

1. Resume the pending Formalizer repair for conformal target-shape drift.
2. Make the Formalizer either preserve the probability/coverage source theorem
   shape or move arithmetic lemmas into support channels.
3. Ensure ProofEngineer consumes local Lean and optional Lean LSP MCP
   `tool_call_trace` inside the next prompt.
4. Promote generated algorithm/simulation prototypes only through explicit
   registry tests and reruns; sandbox execution remains engineering evidence,
   not theorem proof.
5. Add a second task-family capability run, for example FDR, randomization
   variance, KKT/certificate, or empirical-process bound.
