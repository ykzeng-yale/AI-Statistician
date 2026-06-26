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

The next correction keeps Critic in the same architecture. When a formalizer
manifest names unresolved proof blockers, Critic now converts them into typed
`formal_blocker_resource_requests` for Formalizer/ProofEngineer instead of
embedding a theorem-specific repair in runtime Python. The live probe
`runs/main_worker_live_runtime_resume_critic_formal_blocker_requests_probe/research_agent_runtime_manifest.json`
created a pending Formalizer task with 5 requests, including Lean primitive
lookup for `Nat.ceil`, semantic-definition lookup for exchangeability, proof
search for source-to-bridge premise derivation, and Critic agenda follow-ups.
Every request is marked
`FORMAL_BLOCKER_RESOURCE_REQUEST_NOT_PROOF_EVIDENCE`; retrieval hits, LSP
diagnostics, and proof-search suggestions still become proof evidence only if
the exact repaired artifact is checked by local Lean/AXLE.

The follow-up live probe
`runs/main_worker_live_runtime_resume_formal_blocker_request_carry_forward_probe/research_agent_runtime_manifest.json`
exercised request preservation across the next ProofEngineer loop. The runtime
generated one source-to-bridge premise derivation work order, then rejected it
as non-evidence because the candidate missed the required semantic anchors
`hQuantileThreshold`, `hGoodRank`, and `hExch`. Its local Lean repair feedback
carried the original 5 requests forward and synthesized a sixth typed request
for unknown identifier `Finset.univ.filter`. This is the intended design shape:
the LLM may propose proof objects, but runtime validators and Lean diagnostics
convert unresolved resources into typed retrieval/prover work without claiming
proof.

The next live sequence showed a separate integration boundary. The
formal-environment bridge received work orders for missing primitives such as
`coverage_event`, `good_rank_event`, and `C_n`, but no exact source-theorem
candidate artifact existed for signature probing. Treating that as a generic
`candidate_artifact_path missing` failure was too vague: it did not tell
Formalizer/ProofEngineer that the next obligation is to materialize an exact
Lean candidate before Lean signature probes or proof-body execution can run. The
bridge now emits typed non-proof statuses:
`source_theorem_candidate_materialization_required` and
`SIGNATURE_PROBE_BLOCKED_NEEDS_CANDIDATE_ARTIFACT` for absent candidates, or
`source_theorem_candidate_artifact_missing` when the path points nowhere. The
runtime learning export carries the same materialization contract. This is an
evidence-boundary contract, not a conformal theorem heuristic: it prevents
proof-body work from being queued until the LLM/prover stack has produced a
concrete candidate artifact that local Lean/AXLE can inspect.

The follow-up correction keeps that contract alive across long resume chains.
Runtime memory compaction now pins candidate-materialization blocker rows, the
resume-context merge remains bounded by `max_rows`, and Critic recomputes its
proof-bank summary from the current runtime memory before issuing
Formalizer/ProofEngineer feedback. The live bounded probe
`runs/main_worker_live_runtime_resume_critic_materialization_request_bounded_probe/research_agent_runtime_manifest.json`
ended at the expected `42/49` scorecard gate with
`runtime_learning_memory.rows_loaded=20`, 4 pinned materialization rows, and a
pending FormalizationEvaluator task carrying
`SOURCE_THEOREM_CANDIDATE_MATERIALIZATION_REQUIRED`. This is still
non-evidence orchestration; it tells Claude/ProofEngineer/prover adapters to
materialize an exact Lean candidate artifact before signature probes or
proof-body work, rather than letting AgentRuntime invent another local repair.

The next live turn consumed that handoff far enough to materialize a concrete
source-theorem-shaped Lean artifact and project-local proof-state mirror, then
local Lean rejected it with `lean_parser_or_syntax_error`. That is the desired
architectural direction: the blocker has moved from absent artifact to exact
artifact repair, while proof evidence remains false. A related generic repair
contract was added for unavailable imports: when candidate precheck or local
Lean reports an unavailable Lean module, the runtime now emits a typed
`lean_unavailable_import` resource request with suggested replacement modules
when the validator has them. This routes import/API lookup to formal-source
retrieval, Lean LSP/MCP, and local Lean/AXLE rather than teaching AgentRuntime a
task-family-specific workaround.

The following ProofEngineer turn repeated the same exact-candidate parser
failure, which exposed a memory-fidelity issue rather than a statistical theorem
rule. Runtime learning rows and proof-bank repair summaries did not consistently
carry `target_lean_declaration` plus target file/line/column for failed
Formalizer Lean candidates. That metadata is now preserved through learning-row
export, CLI memory compaction, runtime memory replay, and proof-bank summary
projection. The goal is architectural: future Critic/ProofEngineer turns should
know that a concrete exact target artifact exists and failed local Lean at a
specific declaration/location, instead of falling back to older
candidate-materialization-required memory.

The patched live replay of that failure exposed the next generic control
boundary: after a retry, the LLM can still emit another broad parser-failing
Lean theorem. AgentRuntime should not learn a theorem-specific workaround for
that. It now escalates repeated `lean_parser_or_syntax_error` feedback into a
typed `lean_repeated_parser_or_syntax_failure` blocker request, enriches the
local-Lean repair contract with a fail-closed/minimal ASCII-core-Lean rule, and
keeps the request marked
`FORMAL_BLOCKER_RESOURCE_REQUEST_NOT_PROOF_EVIDENCE`. This makes the mature
prover/RAG pattern explicit: inspect the exact artifact and diagnostics, use
formal-source/prover tools for a smaller syntax-valid support lemma or
dependency, rerun local Lean/AXLE, or record the source theorem as
`FORMAL_GAP`. It is loop control and proof-boundary enforcement, not a
hardcoded conformal proof strategy.

The subsequent repairs keep the same design boundary. `Type*` is now treated as
a local Lean parser-compatibility error because this project's Lean invocation
rejects it; active repeated-syntax contracts also reject another executable
source-theorem candidate in the `formal_targets` channel until the model has
either fail-closed the source theorem or moved to a support-helper channel.
When the model does fail-close a source theorem, the normalizer removes
`sorry`/placeholder Lean sketches so a `FORMAL_GAP` cannot masquerade as kernel
work. Finally, stale carried diagnostics are refreshed into current repair
contracts: no-import helpers that fail on `Real`, order notation, arithmetic
tactics, `Finset`, `MeasureTheory`, or `ENNReal` are routed to a core-Lean-only
`Prop` helper contract unless the prover stack supplies a verified import. This
is still generic runtime loop control for Claude plus Lean/RAG/OpenProver
adapters; it does not add a special proof of
`split_conformal_finite_sample_coverage` to Python.

The compiled-helper follow-up added one more boundary fix. A no-import core
`Prop` helper can be useful diagnostic evidence after local Lean compiles it,
but warnings on a successful exit must not become `lean_local_check_failed`
repair contracts in runtime memory. The replay classifier now builds repair
contracts only from failed prechecks or failed verifier exits. The same live
chain also exposed a Lean environment diagnostic shape from Critic-owned
formal-subclaim checks: `Mathlib.olean` missing as an object file. That is now
classified as `lean_import_environment_missing` and routed as a typed
`lean_unavailable_import` blocker request from Critic feedback. This keeps the
fix in the prover/RAG/import-resolution lane, not in theorem-specific runtime
logic.

The follow-up run from that typed import handoff exposed the remaining design
gap: the Formalizer/ProofEngineer turn respected the handoff structurally, but
still satisfied capability pressure by emitting a no-import helper over `Real`
and `linarith`. That is exactly the kind of mature-prover rule the runtime should
not rediscover by repeated failure. The contract now promotes the Mathlib-root
environment blocker into a generic no-import core-helper gate: if the agent has
not verified a narrow import in the configured Lake project, helper candidates
may use only core Lean `Prop`/arrow/`exact` structure and are prechecked before
artifact materialization. The prompt compactor also preserves these repair keys
instead of dropping them after generic context truncation. This is a reusable
Claude-plus-Lean/RAG orchestration rule, not a hand-coded conformal proof step.

The live replay after this patch moved in the right direction: the
ProofEngineer emitted a no-import core `Prop` implication helper and local Lean
compiled it. AgentRuntime still marked it as diagnostic-helper evidence only,
not source-theorem proof, and routed onward to Critic. The remaining failure
mode is now appropriately semantic rather than syntactic/import-level: the
source-to-bridge derivation must connect `hGoodRankImpliesCovered` to exact
source anchors such as `hQuantileThreshold` and `hExch`. That is the right
handoff for TheoryDeveloper/Formalizer/ProofEngineer plus formal-source
retrieval, because it asks the system to derive or retrieve the missing theorem
structure instead of accumulating local Lean corner-case rewrites.

The next live Critic handoff exposed the same problem at a more architectural
level: source-theorem proof-body adapter failures were present in runtime
learning rows and the latest proof-bank summary, but the next Formalizer repair
task received `source_theorem_proof_body_adapter_feedback=null`. That kind of
feedback loss is what forces AgentRuntime to grow hardcoded rescue rules. The
runtime now carries a compact
`source_theorem_proof_body_adapter_feedback` object through Critic repair
feedback, converts unverified adapter residuals into typed formal blocker
resource requests, preserves the object in the Formalizer prompt, and pins
adapter/proof-route feedback rows in rolling runtime memory. This is intended
as a reusable proof-route contract: Claude and prover/RAG adapters receive the
actual bridge failure, artifact path, declaration, and diagnostics, while the
evidence boundary still says adapter rows are not full source-theorem proof.
