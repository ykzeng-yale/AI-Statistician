# AI Statistician Agent Runtime Goal

## Objective

Build a live, autonomous AI Statistical Theory Lab whose own runtime can turn a
fresh statistical research question or paper into rigorous theory, executable
scientific code, simulations, exact Lean targets, proof attempts, revisions, and
an honest final evidence record.

Claude, OpenAI, or another model is a replaceable reasoning backend inside the
system. The product is the combination of model capacity, direct tool access,
artifact memory, isolated environments, independent review, and exact evidence
authority. It is not a thin wrapper around an external coding-agent CLI, an
answer registry, or a collection of audit queues.

Complete coding-agent CLIs such as Codex or Claude Code are not normal pure-LLM
providers: if integrated, their tool actions must pass through explicit adapters
with the same sandbox, artifact, budget, and evidence contracts.

## Success Condition

For a fresh task, one immutable lineage must demonstrate:

```text
question/paper
  -> model-authored problem formulation and theory workspace
  -> model-authored Python or R executed in the scientific sandbox
  -> independent semantic review and frozen simulation protocol
  -> fresh simulation observations and theory/code revision when needed
  -> exact model-authored Lean target and source
  -> task-bound formal RAG plus live Lean state/compiler feedback
  -> independent exact-statement review
  -> exact source hash rerun through the Lean kernel gate
  -> final critic and explicit remaining gaps
```

The runtime is fully end to end only when this closes on multiple unrelated
development families and transfers to a sealed held-out panel without adding
family-specific rules. The current system has not met that condition.

## Canonical Roles

### AgentRuntime

Owns typed scheduling, content-addressed artifacts, tool execution, resource and
permission policy, hashes, checkpoints, lineage budgets, and evidence labels. It
has one endpoint and no post-runtime execution plane.

### Architect

Creates the initial research graph, resolves genuine cross-workspace conflicts,
chooses a new owner after a workspace budget is exhausted, and decides whether
to continue or stop. It is not a message router for ordinary compiler, ABI,
simulation, or Lean errors.

### TheoryDeveloper

Owns definitions, estimands, procedures, assumptions, equation derivations,
lemma dependencies, counterexamples, theorem candidates, and revision lineage.
A compact JSON packet indexes this workspace; it is not the whole theory.

### Scientific Source Agents

AlgorithmEngineer and SimulationEngineer own complete Python or R source. The
same model chooses tools, sees raw sandbox observations, and writes complete
replacement source until acceptance or budget exhaustion.

### Formalizer/ProofEngineer

Owns the complete Lean source and chooses retrieval, proof-state inspection,
proof-candidate search, editing, and checking actions. The harness never writes
imports, tactics, proof bodies, or grammar fixes. Mathlib/Statlib conventions and
existing proofs arrive through RAG and the active Lean environment.

### Independent Reviewers

Report source-grounded semantic findings. They cannot execute code, claim proof,
select a repair owner, or route the next task. The Architect owns cross-workspace
routing; the source author owns local revisions.

### Critic and Authorities

Critic judges the complete research record. The scientific sandbox authorizes
execution claims, the frozen metric evaluator authorizes its registered empirical
gates, and Lean/AXLE/kernel authorizes formal proof claims. No subsystem can
promote its own proposal.

## Direct Workspace Contract

Every source workspace follows:

```text
LLM action -> exact tool execution -> raw observation -> same LLM revision
```

The harness may validate schemas and ask the same model to regenerate a complete
packet. It may not synthesize missing semantic content. Routine failures stay in
the owning workspace. Only exhausted budgets, inconsistent upstream artifacts,
or conflicts between independent authorities return to Architect.

Persistent control state should use references:

```text
TaskRef: id, owner, objective_ref, workspace_ref, budget
ArtifactRef: id, path, hash, type
Observation: tool, status, stdout_ref, stderr_ref, artifact_hash
Decision: action, target_ref, rationale_ref
```

Substantive artifacts are stored once. Tasks and traces must not recursively copy
prior tasks, deferred tasks, complete source, and nested manifests.

## Non-Negotiable Boundaries

- No task-family formulas, aliases, expected answers, or thresholds in canonical
  runtime, authoring, review, or prover paths.
- No Python middleware that parses Lean errors into source edits or tactics.
- No repair agent, bridge hierarchy, patch queue, or hidden fallback scheduler.
- No automatic post-result mutation of a frozen empirical protocol.
- No retrieval hit, pseudo-formal block, LLM judgment, or weaker compiled theorem
  counted as exact theorem proof.
- No Opus. Production has a Sonnet ceiling; all tests/evaluations use exact Haiku.
- No held-out-driven rules. Held-out outcomes stay sealed until development
  closure and may evaluate transfer only.

## Evaluation Ladder

1. Unit and replay tests validate transport and authority mechanisms.
2. Component live probes validate one direct workspace with real tools.
3. Development-panel runs validate the complete same-run lineage on unrelated
   statistical families.
4. Held-out runs evaluate transfer without code or prompt changes derived from
   their expected answers.
5. Broader paper benchmarks evaluate ingestion, theory depth, reusable library
   growth, and research-policy learning.

Audit scores, manifest counts, support lemmas, and component probes cannot
substitute for a higher rung.

## Current Priority

The major repair/bridge control planes have been removed. The immediate work is:

1. consolidate the still-large metric protocol implementation while keeping its
   independent reviewer and frozen pre-result authority;
2. build the persistent TheoryDeveloper equation/lemma/counterexample workspace;
3. run a fresh exact-Haiku two-family development panel through real Python/R and
   Lean environments;
4. fix only shared agent context, tool, feedback, retrieval, and authority
   mechanisms exposed by that run;
5. keep the held-out panel sealed until exact development closure.

See [production_design.md](production_design.md) for implementation detail.
