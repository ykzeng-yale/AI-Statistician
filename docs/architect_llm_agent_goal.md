# AI Statistician Agent Runtime Goal

This document is the canonical goal boundary for AI Statistician.

For parallel work across multiple Codex sessions, read
[`multi_codex_coordination.md`](multi_codex_coordination.md) before starting a
branch. That document records the shared coordination branch, capability
ladder, evidence boundaries, and current blockers.

The target system is not an audit harness, a static frontier benchmark runner,
a deterministic registry executor, or a thin wrapper around a complete external
coding agent. Those pieces can be support infrastructure or model backends. The
target is a full AI Statistician coding-agent system: its own agent runtime,
environment iteration loop, blackboard, artifact store, tool adapters,
validators, memory/RAG substrate, and multi-subsystem orchestration.
Claude/OpenAI/Gemini-style API models should be replaceable generator backends
behind this runtime, not the architecture itself. Complete coding agents such as
Codex, Claude Code, Gemini CLI, or Cursor-style agents are not normal pure-LLM
providers; if used later, they must sit behind explicit tool-worker adapters
with the same evidence, sandbox, and audit boundaries as any other tool.

The runtime must be able to turn an open statistical research question or paper
into proposed methodology, theory, formal proof obligations, code, simulations,
Lean/proof attempts, critiques, revisions, and a reviewable evidence ledger
through repeated plan-act-observe-revise cycles.

## Corrected Goal Statement

The project goal is to build a live Claude/OpenAI generator-backed AI
Statistical Theory Lab whose own `AgentRuntime` and `Architect` control
statistical theory discovery, algorithm/simulation environment execution,
formalization, ProofEngineer Lean/AXLE attempts, critique, memory, and
rerouting.

The runtime succeeds only when it can start from an open statistical question or
paper, create and revise statistical theory/procedures in an environment loop,
and report which claims are source-grounded, simulated, kernel-verified, or
still formally open. It is not enough for the system to pass broad audits, emit
prompt packets, create queues, retrieve Lean declarations, or prove helper
lemmas unless those artifacts are consumed by the Architect-controlled loop and
change the next statistical action.

The central design correction is to keep these roles separate:

- `AgentRuntime` is the operating system: task scheduling, blackboard state,
  tool execution, observations, failure recovery, and stop rules.
- `Architect` is the controller: next subsystem, budget, reroute, acceptance
  gate, and stopping condition.
- LLM workers are generator backends: they propose theory, code, proof plans,
  critiques, and repairs, but do not own tool execution or evidence promotion.
- Validators are gates: Lean/AXLE, sandbox tests, source review, semantic
  checks, and hidden evals accept, reject, or downgrade proposals.
- Audits, RAG package checks, release bundles, and static benchmarks are
  support telemetry. They must not become the main system.

## Target System

The intended runtime shape is:

```text
Open research question or paper
  -> AgentRuntime / Blackboard
       task dispatch, artifact versions, memory/RAG, tool policy, stop rules
  -> Architect subsystem
       owns project state, next-action policy, rerouting, and acceptance gates
  -> ProblemFormalizer subsystem
       extracts observed data, DGP, estimand, assumptions, asymptotic regime
  -> TheoryDeveloper subsystem
       derives estimator/procedure, theorem candidates, lemma DAG, proof plan
  -> PaperTheoryExtractor subsystem
       extracts paper statements, source spans, dependency DAGs, proof sketches
  -> Retrieval/SearchMemory subsystem
       retrieves papers, theorem templates, Lean/Mathlib/StatInference sources
  -> Formalizer / ProofEngineer / LeanProver subsystems
       translate theorem cards to Lean targets, prove or return formal gaps
  -> AlgorithmEngineer subsystem
       implement or patch algorithms in an isolated sandbox
  -> SimulatorDesigner and deterministic execution subsystem
       design ADEMP-style simulation/stress plans and execute reproducibly
  -> Critic/Evaluator subsystems
       attack assumptions, proof gaps, novelty, simulation design, code drift
  -> AgentRuntime
       observes outputs/failures, updates blackboard, and dispatches revisions
```

The Architect is the controller subsystem. The AgentRuntime is the execution
system that gives the Architect coding-agent capabilities: planning, tool
selection, file/environment interaction, code/proof execution, observation,
failure recovery, task spawning, and iterative revision. The TheoryDeveloper is
the main mathematical engine. Verification, simulation, retrieval, and critics
are acceptance and feedback mechanisms, not substitutes for statistical theory
development.

## Runtime Components

The project must eventually own these layers rather than assuming Codex or any
other single agent provides them:

- `ModelBackend`: interchangeable generator-only adapters for
  Anthropic/OpenAI/Gemini APIs, static replay, and future pure-model APIs.
  Coding-agent CLIs are separate tool-worker adapters, not default LLM providers.
- `AgentRuntime`: plan-act-observe-revise loop, task scheduling, subagent
  spawning, stop conditions, budget policy, and recovery from failed actions.
- `EnvironmentLayer`: filesystem, shell, Python/R/Lean execution, sandbox code
  generation, tests, local databases, paper sources, and proof projects.
- `Blackboard`: shared project state, artifact graph, versioned claims,
  accepted/rejected hypotheses, active blockers, and handoff protocol.
- `SubsystemRegistry`: Architect, TheoryDeveloper, PaperTheoryExtractor,
  AlgorithmEngineer, SimulatorDesigner, Formalizer, LeanProver, RAGSearchMemory,
  SourceAuthority, SemanticReview, Critic, and Evaluator.
- `ToolAdapters`: typed interfaces for shell, files, retrieval, Lean/LSP/AXLE,
  paper ingestion, simulation execution, and code review.
- `Validators`: schema checks, simulation reproducibility, source authority,
  semantic drift checks, hidden benchmark hygiene, and Lean kernel verification.
- `EvidenceLedger`: every proposal, tool call, simulation, proof attempt,
  retrieval hit, critique, and promotion decision with explicit boundaries.

## Current Implementation Boundary

The current production path is useful but not the final system:

```text
OpenResearchQuestion
  -> deterministic ProblemFormalizer
  -> registry/template TheoryPlanner
  -> formal subclaim verifier and formal gaps
  -> vetted algorithm registry
  -> deterministic simulator
  -> audit traces and repair queues
```

This implementation is valuable because it provides provenance, proof
boundaries, retrieval indexes, kernel gates, simulation diagnostics, and
benchmark evidence. But it is still mostly a scaffold plus bounded loop, not
the complete coding-agent runtime above. It is misaligned if it becomes the main
measure of progress. High static coverage, release gates, prompt packets, and
RAG hits do not prove that the system has done frontier statistical research or
that it has run a full environment iteration loop.

## Core Typed Artifacts

The Architect loop should communicate through typed artifacts rather than loose
agent chat:

- `ProjectState`: active problem, artifact versions, accepted claims, rejected
  claims, open blockers, and next-action policy.
- `AgentTask`: owner subsystem, objective, inputs, allowed tools, budget,
  expected artifacts, stop condition, and acceptance gate.
- `RuntimeIterationTrace`: plan, action, environment observation, failure
  classification, revised plan, and produced artifacts.
- `ToolCallRecord`: command or API call, inputs, output paths, hashes, exit
  status, stderr/stdout summary, and safety boundary.
- `EnvironmentObservation`: test result, simulation metric, Lean diagnostic,
  retrieval result, filesystem diff, or critic finding used for replanning.
- `ProblemCard`: observed data, DGP, estimand, assumptions, asymptotic regime,
  desired theorem type, and novelty query.
- `TheoryDerivationPacket`: deductive derivation from problem to candidate
  estimator/procedure/theorem, including equations and self-critique.
- `EstimatorSpec`: inputs, nuisance estimators, algorithm, tuning, output, and
  implementation constraints.
- `TheoremCard`: precise informal theorem, assumptions used, conclusion, rate
  or limit law, proof strategy, and semantic risks.
- `LemmaCard`: statement, dependencies, used-by links, and formalization
  difficulty.
- `ProofPlan`: theorem-to-lemma DAG, proof techniques, required primitives,
  and acceptable/unacceptable formalization changes.
- `FormalizationRequest`: Lean target scope, intended theorem strength,
  definitions, imports, and semantic alignment constraints.
- `ProofObligationReport`: kernel status, failed goals, missing assumptions,
  proved subclaims, semantic mismatch, and feedback to TheoryDeveloper.
- `SimulationADEMPSpec`: aims, DGPs, estimands, methods, performance measures,
  sample-size grids, stress tests, and expected theorem behavior.
- `EmpiricalAnomalyReport`: mismatch between theorem predictions and simulator
  behavior, likely cause, and reroute recommendation.
- `AlgorithmPatchArtifact`: generated code or patch, tests, implementation
  hash, before/after metrics, and promotion gate.
- `EvidenceLedger`: source, simulation, formal, kernel, retrieval, and critic
  evidence with explicit proof boundaries.

## LLM TheoryDeveloper Contract

For every frontier theory task, the LLM TheoryDeveloper must do real
deductive statistical work. It should not only classify a question.

Minimum output:

1. Problem parse: observed data, latent objects, DGP, estimand, nuisances,
   asymptotic regime.
2. Candidate procedure: estimator/test/procedure, formula, algorithm sketch,
   tuning, and computational constraints.
3. Assumptions: statement, role, where used, and failure mode if violated.
4. Derivation chain: equation-level decomposition of bias, variance, risk,
   coverage, rate, limiting distribution, or certificate.
5. Theorem candidates: precise informal statements, assumptions, conclusion,
   rate/constants/regime, and proof strategy.
6. Lemma DAG: intermediate lemmas, dependencies, and proof techniques.
7. Simulation predictions: diagnostics implied by the theorem and stress tests
   expected to break assumptions.
8. Formalization obligations: Lean targets, missing primitives, source theorem
   candidates, and semantic risks.
9. Self-critique: theorem too strong, hidden regularity, measurability,
   positivity, exchangeability, integrability, or finite-sample risks.
10. Rejected alternatives: why easier or more standard methods were rejected.

LLM theory output is derivation evidence, not proof evidence. It can be accepted
only as a proposal until source grounding, simulation, semantic review, and
Lean/AXLE kernel checks support the relevant claims.

## How External Ideas Fit

External papers and tools should be incorporated only when they strengthen the
Architect loop:

- DAP-style discover-and-prove strengthens the TheoryDeveloper stage by
  separating answer discovery from proof of a fully specified target.
- RMA-style research math agents strengthen the Architect stage by forcing
  problem analysis before retrieval, dynamic knowledge-bank construction,
  fair comparison against analogous theorem families, and proposer/verifier
  refinement loops. These rows are long-horizon routing and review memory,
  not theorem proof evidence.
- MerLean-style paper extraction strengthens paper-to-theory ingestion by
  extracting statement catalogs, dependency DAGs, Lean candidates, and
  Lean-to-LaTeX roundtrip review.
- Certificate-checking patterns strengthen proof scalability by letting agents
  generate witnesses checked by small Lean kernels.
- Lean RAG, dependency graphs, LSP, OpenProver, AXLE, and proof-search tools
  strengthen Formalizer/ProofEngineer feedback, but retrieval hits are never
  proof evidence by themselves.

Resources that only add another audit, monitor, or static score without feeding
the Architect's action policy should be treated as low priority.

## Corrected Blueprint

The blueprint is a single closed loop, not a collection of independent audits:

```text
Open statistical question or paper
  -> AgentRuntime creates ProjectState on the Blackboard
  -> Architect performs problem analysis and sets the next-action policy
  -> ProblemFormalizer / PaperTheoryExtractor builds StatTheory IR
       DGP, estimand, assumptions, regime, source theorem DAG
  -> RAG/SearchMemory builds dynamic StatKnowledgeBank
       paper analogies, theorem families, Lean/Mathlib/StatInference hits,
       proof memory, failed attempts, fair-comparison notes
  -> TheoryDeveloper proposes theory
       estimator/procedure, theorem cards, derivation chain, lemma DAG,
       simulation predictions, proof obligations, rejected alternatives
  -> SimulatorEngineer designs adversarial stress tests
       DGP mismatch, hidden assumption violations, finite-sample regimes,
       theorem-prediction vs empirical behavior checks
  -> AlgorithmEngineer implements or patches executable artifacts
       sandbox code, tests, diagnostics, hashes, promotion blockers
  -> Formalizer translates selected theorem cards into Lean targets
       semantic alignment, source spans, formal gaps, exact target identity
  -> ProofEngineer / LeanProver works inside the runtime
       reads Lean goals, retrieves premises, attempts proofs, runs local
       Lean/AXLE, records residual goals, writes kernel results to memory
  -> Critic/Evaluator attacks the result
       false analogy, hidden assumptions, semantic drift, weak theorem,
       simulation flaw, proof gap, implementation drift
  -> EvidenceLedger records typed evidence and boundaries
  -> Architect reroutes until source theorem proved, accepted with explicit
     gaps, rejected, or budget exhausted with honest blockers
```

The current split-conformal source-theorem path is a useful first stress test,
but it must not define the whole goal. It should become the first verified
ProofEngineer skill in the runtime, then be followed by at least one unrelated
statistics task such as randomization variance, FDR/multiple testing, KKT or
convex-estimator certificates, or privacy accounting. Cross-task transfer is a
core requirement for the AI Statistician claim.

## Core Completion Gates

These gates define what counts as progress toward the final system:

1. Live generator-backed loop: Architect, TheoryDeveloper, SimulatorEngineer,
   AlgorithmEngineer, Formalizer/ProofEngineer, and Critic can run with
   supported Anthropic/OpenAI generator backends. Static replay is a plumbing
   test only.
2. Architect control: no successful main-capability run may bypass the
   Architect, and `ACCEPTED` must mean only runtime agenda acceptance unless a
   kernel proof gate says more.
3. Environment execution: generated code/proof artifacts are executed by the
   runtime in controlled sandboxes or Lean projects, with observations written
   back to the blackboard.
4. Internal ProofEngineer loop: proof-body queues, adapters, premise
   derivations, local Lean/AXLE checks, residual goals, and proof repair must be
   consumed inside `AgentRuntime`, not left as disconnected post-run CLI
   artifacts.
5. Source-theorem evidence: helper proofs, bridge proofs, theorem-reduction
   closures, and compiled candidate definitions remain support evidence until
   the exact source theorem or a reviewed theorem-equivalent target is kernel
   verified.
6. Paper and literature grounding: paper ingestion must produce source spans,
   statement catalogs, dependency DAGs, fair-comparison notes, and StatTheory IR
   that the Architect can use in subsequent actions.
7. Cross-task capability: at least two unrelated frontier-statistics tasks must
   show live theory, simulation/code, formalization, proof feedback, memory, and
   reroute behavior. A single conformal proof path is insufficient.

## Anti-Drift Rules

When choosing future work, prefer edits that make the closed loop more real:
live generator proposal, environment action, verifier observation, memory
update, and Architect reroute. Defer edits that only add another monitor,
package audit, static score, or publication artifact unless they directly feed
the Architect's next action or prevent a known evidence-boundary bug.

The system is drifting when status reports emphasize `audit passed`, `contract
ok`, `RAG healthy`, `queue ready`, `ACCEPTED`, or `static E2E` without also
reporting live-generator status, Architect participation, environment
execution, source-theorem kernel evidence, formal gaps, and the next runtime
owner.

## Immediate Implementation Priority

The next aligned implementation work is not another release gate. It is:

1. Stabilize the canonical baseline: work from a clean, current checkout or a
   named dirty branch so runtime/proof changes are not confused with old
   planner/audit edits.
2. Make ProofEngineer an internal runtime worker for the current
   `split_conformal_coverage` exact proof-body loop: read the reached Lean goal,
   derive or import missing adapter/premise obligations, rerun local Lean/AXLE,
   and write source-theorem evidence or residual goals back to memory.
3. Add a compact `ProjectState`/`EvidenceLedger` truth table to the runtime:
   proposal, retrieval, simulation, helper-kernel proof, theorem-reduction
   proof, source-theorem proof, and formal gap must be distinct states.
4. Run one fresh live Architect-enabled Claude/OpenAI end-to-end task in strict
   capability mode. Static/no-Architect/no-proof runs cannot be used as main
   capability evidence.
5. Add a second frontier-statistics task line and require the same loop to
   generate theory, run simulation/code, formalize obligations, and produce
   proof or explicit gaps.
6. Move external LLM context export approval to the shared `ModelBackend` or
   `AgentRuntime` boundary so every worker follows one approval and redaction
   policy.
7. Promote MerLean-style paper extraction only after the live runtime can
   consume the extracted StatTheory IR and route actions from it.

The existing deterministic implementation should remain as a fallback,
regression testbed, and evidence boundary. It should not be the main engine of
theory discovery or the substitute for a full coding-agent runtime.

## Capability Anti-Substitution Rules

The project goal must not be redefined around artifacts that are easier to test
than the live agentic system. In main capability evaluation:

- Static/replay providers are forbidden. They are unit-test fixtures for
  schema, manifest, and plumbing coverage only.
- No-Architect runs are forbidden. The Architect must choose and justify the
  research path, evidence gates, reroutes, and stop conditions.
- Deterministic fallback planners, registered templates, proof-bank shortcuts,
  and hard-coded theorem-specific pattern matches may preserve safety,
  regression coverage, or explicit `INCOMPLETE` status, but they cannot count as
  statistical research ability.
- Manual proof filters and manual research-path overrides are debug or
  controlled-smoke tools. They cannot stand in for autonomous path selection in
  capability claims.
- A fallback may keep the system honest by refusing to promote evidence, but it
  must not silently substitute for LLM TheoryDeveloper, Simulator, Algorithm,
  Formalizer, ProofEngineer, Critic, or Architect work.
- Capability summaries must separate live-agent capability from scaffold
  health. Static pass, fallback contract, queue creation, RAG hit, simulation
  run, or helper proof is not proof that the AI Statistician can do open
  statistical research.

Initial runtime contracts and the small dispatch loop live in
`ai_statistician/agent_runtime.py`. The first project-specific runtime bridge
lives in `ai_statistician/research_agent_runtime.py`: it dispatches
`RetrievalMemory -> TheoryDeveloper -> SimulationEvaluator ->
AlgorithmEngineer -> FormalizationEvaluator -> CriticEvaluator`, records
blackboard artifacts, paper/knowledge/formal-source retrieval context,
simulation tool calls, algorithm sandbox prototype runs, formal
subclaim/proof-gap feedback, next-action agenda items, learning rows, and
evidence rows. This is still only the first runtime slice. It needs broader
AlgorithmEngineer code-generation adapters, stronger sandbox execution policies,
LeanProver repair loops, retrieval-backed formalizer planning, and model-backed
replanning before it can be considered the full AI Statistician runtime.

## Non-Negotiable Evidence Boundaries

- RAG hits are source suggestions, not proof evidence.
- Simulation is empirical stress evidence, not theorem proof.
- LLM derivations are mathematical proposals, not verified results.
- Lean typechecking of a weak or drifted statement does not prove the intended
  paper theorem.
- Only AXLE/local Lean kernel verification can count as formal proof evidence.
- A proved helper or certificate checker does not prove a full frontier theorem
  unless the theorem reduction is also verified.
