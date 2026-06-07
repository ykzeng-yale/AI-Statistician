# AI Statistician Agent Runtime Goal

This document is the canonical goal boundary for AI Statistician.

The target system is not an audit harness, a static frontier benchmark runner,
a deterministic registry executor, or a thin wrapper around a complete external
coding agent. Those pieces can be support infrastructure or model backends. The
target is a full AI Statistician coding-agent system: its own agent runtime,
environment iteration loop, blackboard, artifact store, tool adapters,
validators, memory/RAG substrate, and multi-subsystem orchestration. Codex,
Claude Code, OpenAI API models, Gemini CLI, Cursor-style agents, or future
coding agents should be replaceable workers behind this runtime, not the
architecture itself.

The runtime must be able to turn an open statistical research question or paper
into proposed methodology, theory, formal proof obligations, code, simulations,
Lean/proof attempts, critiques, revisions, and a reviewable evidence ledger
through repeated plan-act-observe-revise cycles.

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

- `ModelBackend`: interchangeable adapters for local Codex-like models,
  Anthropic/OpenAI/Gemini APIs, CLI agents, and future coding-agent workers.
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

## Immediate Implementation Priority

The next aligned implementation work is not another release gate. It is:

1. Define the `AgentRuntime` contracts: `ModelBackend`, `AgentTask`,
   `RuntimeIterationTrace`, `EnvironmentObservation`, `ToolCallRecord`,
   `Blackboard`, and `EvidenceLedger`.
2. Promote `ResearchArchitectAgent` from a one-shot artifact exporter into an
   Architect subsystem that dispatches tasks through the runtime.
3. Add an LLM-backed `TheoryDeveloper` subsystem with a rigorous derivation
   prompt, response validator, memory inputs, and failure-feedback loop.
4. Route frontier/open tasks through
   `Architect -> TheoryDeveloper -> Algorithm/Simulation/SymbolicDerivation ->
   Formalizer/LeanProver -> Critic/Evaluator -> Architect reroute`
   before deterministic fallback.
5. Require environment iteration artifacts: generated code/proof attempts,
   commands, simulation outputs, Lean diagnostics, diffs, and replanning
   decisions.
6. Score whether accepted LLM/runtime iterations improve hidden frontier target
   recovery, simulation behavior, source alignment, and downstream formal proof
   progress.

The existing deterministic implementation should remain as a fallback,
regression testbed, and evidence boundary. It should not be the main engine of
theory discovery or the substitute for a full coding-agent runtime.

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
