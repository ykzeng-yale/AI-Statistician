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

## Follow-Up Evidence

The first extraction is complete in `ai_statistician/source_to_bridge_metadata.py`.
The live keyed probe
`runs/main_worker_live_runtime_resume_metadata_request_artifact_probe_keyed/research_agent_runtime_manifest.json`
then authored one complete
`SourceToBridgePremiseDerivationCandidateRequest` while producing zero
executable source-to-bridge work orders in the same iteration. That is the
intended separation: metadata can guide a later Formalizer/ProofEngineer
candidate, but it is not proof evidence and cannot certify a helper theorem by
itself.

The follow-up request-consumption probes then exposed the next generic boundary:
the model can emit an executable premise candidate while forgetting to copy the
request object. The runtime now preserves that nested request through
Formalizer memory compaction and autofills it only in the unambiguous
single-request/single-candidate case. The subsequent live failure moved from
missing source-binding metadata to missing semantic-anchor references, with zero
work orders emitted. That is the desired direction: typed request propagation
gets the candidate to the real ProofEngineer obligation, while validation still
blocks proof promotion until the candidate uses the semantic anchors and passes
Lean/AXLE.

The next observed blocker was also generic rather than conformal-specific. A
live repair produced a materialized helper rejected by local Lean with unknown
identifier `Nat.ceil`. The runtime already carries this as a
`local_lean_repair_contract`, so the right next step is Lean API grounding
through local formal-source/RAG/prover tools, not a hand-coded conformal
replacement.

One design-level infrastructure mistake was fixed here: generated Lean files
under `runs/` were valid for `lake env lean` replay but invalid for Lean LSP/MCP
inspection because they had no Lean-project ancestor. Runtime materialization now
keeps the canonical `runs/` artifact for kernel/audit replay and writes an
ignored project-local mirror under
`<lean_project>/.lake/ai_statistician_formalizer_candidates` for proof-state
tooling. The repair context records both paths and preserves the proof boundary:
only the exact kernel/audit artifact can become proof evidence after local
Lean/AXLE verification; the project-local mirror is diagnostic/search context.

The next design correction keeps the `Nat.ceil`-style unknown-API failure from
becoming another hardcoded repair. Formalizer/ProofEngineer repair feedback now
uses the configured formal-source retriever to attach bounded declaration hits
directly inside `proofengineer_repair_context`. The hits are prompt-visible next
to `retrieval_query_seeds`, but every hit is explicitly marked
`FORMAL_SOURCE_RETRIEVAL_GROUNDING_NOT_PROOF_EVIDENCE`; a replacement only
matters after local Lean/AXLE verifies the exact repaired artifact. This restores
the intended architecture: contracts say "do not invent; verify or gap", while
formal-source/RAG/prover adapters supply candidate APIs and premises.

The live audit probe
`runs/main_worker_live_runtime_resume_formal_source_grounding_audit_probe/research_agent_runtime_manifest.json`
confirmed the new observation path: the Formalizer/ProofEngineer turn recorded
5 grounding query groups and 9 formal-source hits, all tagged as non-proof
grounding. The model did not promote a new unverified helper. It fail-closed the
source theorem as `FORMAL_GAP`, named `Nat.ceil` and exchangeability-definition
blockers, and routed to Critic/next-action planning. That is still not a source
theorem proof, but it is the desired architectural behavior for an unresolved
Lean API dependency.
