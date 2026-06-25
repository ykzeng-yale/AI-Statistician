# Runtime Design Drift Audit - 2026-06-25

This note records the design-level check requested during the main-worker
runtime/evaluation lane. It should guide future Codex workers before adding
more runtime-specific repairs.

## Bottom Line

The intended architecture is still correct:

```text
Open statistical question or paper
  -> AgentRuntime / Blackboard
  -> Architect-controlled next-action policy
  -> TheoryDeveloper derives statistical theory and theorem DAGs
  -> RAG/SearchMemory retrieves papers, Lean, Mathlib, StatInference, OpenProver
  -> Formalizer / ProofEngineer generates and repairs Lean proof artifacts
  -> AlgorithmEngineer and SimulationEngineer generate executable Python/R code
  -> local sandbox, Lean, AXLE, LSP, and critic observations
  -> EvidenceLedger records proposal, simulation, retrieval, kernel proof, or gap
  -> Architect reroutes
```

The current implementation has real progress, but it is drifting toward a
conformal-eval repair machine when core files accumulate one-off rules for the
latest failed live run. `architecture-audit` currently reports
`PARTIAL_LIVE_FEEDBACK_LOOP_WITH_SCOPED_AUTONOMY`, with
`full_autonomous_correct=false`. That is the right status.

## What Is Healthy Hardcoding

Some rules belong in the core runtime because they are evidence invariants:

- Never treat LLM text, retrieval hits, simulations, queues, or helper proofs as
  source-theorem proof evidence.
- Reject or downgrade `sorry`, `admit`, proof holes, placeholder Lean, static
  replay, and template-only outputs in capability evidence.
- Require sandbox execution before code artifacts count as implementation
  evidence.
- Require local Lean or AXLE kernel verification before formal proof promotion.
- Preserve exact source-theorem identity and distinguish helper/bridge claims
  from the intended theorem.

These are not substitutes for intelligence. They are safety rails and evidence
boundaries.

## What Is Design Drift

The following patterns should be treated as architecture debt:

- `research_agent_runtime.py` is overgrown. It is now a 37k-line mixture of
  runtime scheduling, manifests, eval scorecards, proof-specific work orders,
  prompt-memory compaction, and task-family repair policy.
- `formalizer_llm.py` contains many conformal/source-to-bridge/Mathlib-import
  special cases. Some protect proof boundaries, but many are local responses to
  one live failure trajectory.
- Algorithm and simulation prompts contain coverage-specific repair advice such
  as widening finite intervals. That can pass a gate without showing general
  statistical coding ability or utility tradeoff reasoning.
- The system has many RAG and prover adapter artifacts, but too many remain
  audit-side outputs instead of live observations consumed by ProofEngineer in
  the same AgentRuntime loop.
- TheoryDeveloper is still too weak relative to the product goal. It should
  emit derivation chains, assumption usage, lemma DAGs, simulation predictions,
  and rejected alternatives, not just compact classification or short theorem
  cards.
- Capability scores are currently dominated by one conformal path. Cross-task
  transfer is not established.

## Design Correction

Future work should move from hardcoded repairs to typed, reusable interfaces:

1. Keep `AgentRuntime` generic.
   It should schedule tasks, execute tools, update blackboard state, write
   evidence, handle retries, and enforce stop rules. It should not know the
   internal proof strategy for `split_conformal_coverage`.

2. Let `Architect` own policy.
   Path choice, proof-first versus simulation-first routing, capability mode,
   and acceptance gates should be Architect artifacts, not scattered conditionals.

3. Move task-family knowledge into skills or policy packs.
   Conformal coverage, causal AIPW, empirical-process, multiple-testing, convex
   optimization, or privacy-accounting rules should live in declarative
   task-family modules with schemas and acceptance gates. Core runtime should
   load them through a registry.

4. Use external mature prover/RAG infrastructure through adapters.
   Loogle, Lean Finder, LeanDojo/ReProver, OpenProver, local Lean/LSP, AXLE, and
   the shared Lean RAG graph should return typed observations. The system should
   not rebuild their retrieval/proof-search logic inside `research_agent_runtime.py`.

5. Strengthen the LLM worker contracts.
   Claude/Sonnet should be asked to do the actual hard work: derive theory,
   write equations, propose theorem DAGs, generate Python/R code, generate Lean,
   read tool diagnostics, and repair artifacts. Runtime code should validate and
   route those proposals, not replace them with Python-side theorem heuristics.

6. Make evaluation adversarial, not prompt-shaping.
   Capability evals should measure whether the same loop works across unrelated
   tasks. They should not add more target-specific prompt patches until the
   system passes one narrow benchmark.

## Immediate Main-Worker Rule

Do not add another conformal-specific branch to the core runtime unless it is
one of these:

- an evidence-boundary guard,
- a typed artifact schema needed by multiple proof routes,
- a migration step that moves a rule out of core runtime and into an adapter,
  policy pack, or task-family module,
- or a failing test that proves the runtime was falsely promoting evidence.

The current source-to-bridge metadata request channel is acceptable only as a
typed orchestration artifact, not as proof evidence and not as another proof
heuristic. Its next design improvement should be extraction from
`research_agent_runtime.py` into a reusable proof-route artifact module or
ProofEngineer adapter contract.
