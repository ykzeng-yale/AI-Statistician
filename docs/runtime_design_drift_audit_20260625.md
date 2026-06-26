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
- Algorithm and simulation prompts previously contained coverage-specific
  repair advice such as widening finite intervals. That can pass a gate without
  showing general statistical coding ability or utility tradeoff reasoning.
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

The generated-code metric repair prompt debt is now partially paid down in
`ai_statistician/generated_metric_repair_policy.py`. AlgorithmEngineer,
SimulationEngineer, and their component repair evals share one domain-neutral
metric-repair contract: repair the estimator/DGP/uncertainty/metric
calculation, keep probability metrics valid when requested, preserve utility
diagnostics such as width, bias, RMSE, efficiency, or failure rate, and reject
vacuous all-covering fixes. Future task-family packs may specify coverage
targets, but they should not teach the core coding-agent prompt a
benchmark-specific widening shortcut.

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

The next Critic handoff tightened that contract without adding a theorem
shortcut. Some adapter diagnostics are truncated by the time they reach
environment feedback, so an import-environment failure can lose the exact Lean
module name. The runtime now recovers import declarations from the generated
adapter Lean artifact itself and turns them into typed
`source_theorem_proof_body_adapter_unavailable_import` requests. The live probe
`runs/main_worker_live_runtime_resume_critic_after_adapter_feedback_import_named_probe/research_agent_runtime_manifest.json`
preserved 10 non-proof blocker requests and named
`Mathlib.Data.Finset.Sort` plus `Mathlib.Data.Real.Basic` as formal-source
queries for the next Formalizer/ProofEngineer turn. This is still
import/RAG/prover routing context, not source-theorem proof evidence.

The follow-up Formalizer turn showed why that metadata belongs in the bridge
schema itself. The live run
`runs/main_worker_live_runtime_resume_named_adapter_import_consumption_probe/research_agent_runtime_manifest.json`
increased kernel-verified helper/subclaim rows to 48 and compiled Formalizer
candidates to 18, but the source-theorem proof-body adapter still had zero
kernel-verified rows. A replay of the same adapter queue through the patched
bridge now records `adapter_candidate_imports` and exact
`unavailable_import=Mathlib.Algebra.Order.Floor` directly in adapter check rows
and runtime learning rows. That is the intended contract: ProofEngineer bridge
observations carry precise Lean import blockers before Critic summarization or
prompt compaction can truncate diagnostics.

The next Critic replay exposed a subtler evidence-boundary mistake in the
fallback path. When old runtime rows lacked bridge-exported
`unavailable_import` metadata, Critic recovered imports from the generated
adapter artifact and labeled the first recovered modules as exact unavailable
imports. That was too strong: a source file import line is only a candidate for
formal-source/Lean-LSP/local-Lean resolution unless the bridge row or full Lean
diagnostic identifies the missing module. Runtime now separates exact
`source_theorem_proof_body_adapter_unavailable_import` requests from
artifact-only `source_theorem_proof_body_adapter_candidate_import_resolution`
requests. The live probe
`runs/main_worker_live_runtime_resume_critic_after_candidate_import_resolution_probe/research_agent_runtime_manifest.json`
keeps the direct Formalizer handoff non-proof and asks the prover/RAG layer to
resolve `Mathlib.Data.Finset.Sort`, `Mathlib.Data.Real.Basic`, and
`Mathlib.Algebra.Order.Floor` as candidate imports, with `unavailable_import`
left empty, `unavailable_import_exact=false`, and artifact provenance recorded
separately from structured bridge candidate imports. Exact unavailable-import
rows remain available only when structured bridge/diagnostic metadata supplies
the missing module.

The next live consumption/replay confirmed why that distinction must survive
bounded memory. Formalizer/ProofEngineer consumed the candidate-import handoff
and the adapter bridge produced a structured exact
`unavailable_import=Mathlib.Algebra.Order.Floor` diagnostic. The immediate
Critic replay initially lost that fact because resume memory compaction and
proof-bank dedupe treated old truncated adapter rows as equivalent to the new
exact bridge row. That is a design-level bug: when exact tool diagnostics are
evicted or deduped behind stale prompt summaries, the runtime is pressured to
add another local rescue rule. Runtime memory now pins adapter import feedback,
preserves `unavailable_import` and `adapter_candidate_imports` through CLI
compaction, distinguishes adapter import rows in the proof-bank dedupe key, and
prioritizes exact unavailable-import diagnostics over artifact-only candidates
when building Critic handoffs. The patched live replay
`runs/main_worker_live_runtime_resume_critic_after_candidate_import_consumption_exact_import_probe/research_agent_runtime_manifest.json`
routes an exact
`source_theorem_proof_body_adapter_unavailable_import` request for
`Mathlib.Algebra.Order.Floor`, followed by lower-confidence candidate-import
resolution rows. This is still non-proof prover/RAG routing context; it simply
keeps the mature Lean tool observation intact so Claude/ProofEngineer can use
retrieval, LSP/MCP, and local Lean instead of AgentRuntime inventing a theorem
patch.

The next Formalizer/ProofEngineer continuation exposed the same context
fidelity issue one layer later. The exact adapter-import request survived as
top-level environment feedback, but a failed Formalizer precheck rebuilt
`proofengineer_repair_context` only from candidate diagnostics. That left the
ProofEngineer loop without the route-critical adapter feedback inside the
context packet it is instructed to consume. The runtime now mirrors typed
`formal_blocker_resource_requests` and
`source_theorem_proof_body_adapter_feedback` into the ProofEngineer repair
context whenever Lean-candidate/precheck feedback is generated. A replay of the
live failing candidate manifest confirms the context carries all 12 blocker
requests and the exact `Mathlib.Algebra.Order.Floor` unavailable-import adapter
diagnostic. A patched live rerun
`runs/main_worker_live_runtime_resume_exact_floor_import_resolution_context_mirror_probe/research_agent_runtime_manifest.json`
took a different, fail-closed route to Critic rather than exercising the
precheck branch, but its bounded Critic memory still retained the exact Floor
adapter rows. This keeps the architecture honest: typed prover/RAG obligations
travel with the ProofEngineer loop, but they remain non-proof context until a
later local Lean/AXLE run verifies the exact repaired artifact.

The follow-up Critic handoff showed a final control-plane cleanup for this
same blocker. Once exact adapter-import diagnostics survive several resume
cycles, Critic can see multiple rows for the same missing Lean module from
different run directories. The old request fingerprint included the adapter
artifact path, so Formalizer received repeated exact
`Mathlib.Algebra.Order.Floor` resource requests. The request is now canonical
for exact unavailable imports by target theorem plus module; artifact paths are
kept as provenance instead of dedupe identity. The patched live Critic replay
`runs/main_worker_live_runtime_resume_critic_after_floor_context_mirror_deduped_probe/research_agent_runtime_manifest.json`
emits exactly one
`source_theorem_proof_body_adapter_unavailable_import` request for
`Mathlib.Algebra.Order.Floor`, while preserving the repeated adapter
diagnostics as non-proof feedback. This keeps the ProofEngineer/RAG loop focused
on one resource-resolution obligation rather than replaying the same missing
import under multiple artifact paths.

The next Formalizer/ProofEngineer pass produced the first kernel-verified
source-theorem proof-body adapter helper, but exposed another design-level
handoff bug. The verified adapter row was present in
`runtime_learning_rows.jsonl` and the adapter bridge export with
`adapter_kernel_verified=true` and
`kernel_verified_source_theorem_proof_body_adapter_ids`, while the pending
Critic task's bounded runtime memory still had zero verified adapter rows. This
was not a Lean theorem-discovery problem; it was orchestration memory dropping
the prover output before the next agent could use it. Runtime memory retention
now prioritizes kernel-verified adapter feedback above lower-confidence
blockers, gives verified adapter rows their own pin identity instead of letting
verified premise ids dedupe them away, and mirrors the current run's bounded
learning memory into serialized pending tasks. The live Critic continuation
`runs/main_worker_verified_adapter_memory_handoff_critic_live/research_agent_runtime_manifest.json`
confirms the next Formalizer/ProofEngineer handoff carries verified adapter ids
including `source_theorem_proof_body_adapter_check:ff5a994ae6182eae8587`.
This remains non-proof orchestration context: the adapter helper compiled, but
`source_theorem_kernel_verified=false`, so the full conformal source theorem and
frontier theorem remain formal gaps until the exact source theorem target is
verified by local Lean/AXLE.

The first live continuation after that handoff showed the next stage of the
same design problem. The runtime correctly carried verified adapter ids and
created another kernel-verified adapter helper, but the final proof-bank summary
still recommended `source_theorem_proof_body_adapter_required` because an older
"verified premise derivations unblock adapter retry" flag outranked the newer
"proof-body adapter is already kernel verified" fact. That created a loop back
into adapter derivation even though the adapter stage had succeeded. The route
policy now disables premise-unblocked adapter retry once a kernel-verified
source-theorem proof-body adapter row exists, letting
`source_theorem_exact_proof_body_repair` become the next target. Deterministic
recomputation over
`runs/main_worker_verified_adapter_exact_proof_body_followup/conformal_prediction_coverage_runtime_result.json`
now reports `recommended_formalizer_target_mode=source_theorem_exact_proof_body_repair`,
with the verified adapter ids preserved and
`source_to_bridge_adapter_retry_unblocked_by_verified_premises=false`. This is
still orchestration, not proof: the next required artifact is an exact source
theorem proof-body candidate checked by local Lean/AXLE.

The next Critic and Formalizer continuations exposed two serialization bugs in
that exact-proof-body handoff. First, Critic produced correct top-level
`environment_feedback` with `source_theorem_proof_body_adapter_required=false`
and the verified adapter ids, while the nested
`architect_context.environment_feedback` still carried an older
adapter-required view. FormalizationEvaluator overwrote the nested value at run
time, but the serialized pending task was internally inconsistent for other
agents and humans. Critic repair-task construction now refreshes the nested
architect feedback to the same current repair feedback used at top level.

Second, the live Formalizer continuation still exported the newest source
theorem work order as `source_theorem_proof_body_adapter_required` even though
the latest proof-bank summary requested
`source_theorem_exact_proof_body_repair`. The root cause was work-order dedupe:
the exact repair row had the same target-derived work-order id as an older
adapter row, and the merge updated provenance but not `proof_mode`,
`action_type`, queue status, acceptance gate, or explicit `false` booleans such
as `proof_body_adapter_required=false`. Dedupe now allows newer control-plane
mode fields and explicit booleans to replace stale state. The patched live run
`runs/main_worker_exact_proof_body_formalizer_dedupe_fixed_live/research_agent_runtime_manifest.json`
exports one exact source-theorem proof-body repair work order and runs the
exact proof-body executor. The executor correctly fails closed with
`source_theorem_semantic_alignment_unreviewed` and
`source_theorem_kernel_verified=false`: verified adapter ids remain routing
context only, not theorem proof.

The follow-up Critic replay exposed the next design drift: that exact
proof-body executor failure was initially collapsed into generic
`formal_gap:proof_bank_expansion`, even though the live blocker was not "find
more helper proofs" but "review the exact semantic definitions before retrying
the source-theorem proof body." Critic routing now treats
`source_theorem_exact_semantic_definition_repair` as a first-class agenda item,
repair feedback packet, and formal-blocker resource request, with an explicit
proof boundary that semantic review and verified adapter ids are routing
context only, not source-theorem proof evidence. The fresh live manifest is
`runs/main_worker_exact_semantic_definition_repair_critic_live/research_agent_runtime_manifest.json`,
whose pending task
`formalize-critic-repair:conformal_prediction_coverage:5f32ce57` now asks the
FormalizationEvaluator to consume
`source_theorem_exact_semantic_definition_repair_feedback` before any
proof-body retry.

The live FormalizationEvaluator continuation consumed that exact semantic
feedback and advanced the prover queue rather than rediscovering the same
adapter rules: it produced 4 source-lookup work orders, 4 closure review
packets, 4 ProofEngineer repair packets, and 4 Lean repair tasks in
`runs/main_worker_exact_semantic_definition_formalizer_live/research_agent_runtime_manifest.json`.
The design bug exposed by this run was in the integrated runtime authoring
path. Standalone exact semantic-definition authoring could already use Claude,
but `research-agent-runtime` only accepted `none` or `static` for the same
authoring worker, and its prompt packets did not tell the model enough about
the local Lake project constraints. In practice, standalone Claude authoring
generated syntactically valid packets but initially compiled 0/3 local Lean
definition candidates because it guessed unavailable imports and hidden
binders. The runtime now supports explicit live authoring providers behind the
external-export gate, passes through model/tokens/temperature/repair/timeout
controls, includes a Lean environment contract in prompt packets, and
normalizes generated leading `import` lines before materialization. A first
integrated probe then exposed one more runtime-only bug: the integrated config
used `provider=anthropic` as the default `model`, which made the API call ask
for model id `anthropic` and fail 3/3 tasks. The config now keeps provider and
model selection separate, leaving the model blank unless explicitly requested
so the existing Sonnet tier resolver chooses `claude-sonnet-4-6`.

After these patches, the standalone environment-contract run compiled 1/3
definition-only candidates (`coverage_event`), and the integrated run
`runs/main_worker_exact_semantic_definition_integrated_authoring_model_fix_live/research_agent_runtime_manifest.json`
called Anthropic from `research-agent-runtime`, proposed 3/3 valid exact
semantic-definition candidate packets, materialized 3 definition-only Lean
candidates, checked all 3 locally, and compiled only `coverage_event`. This is
intentionally not proof promotion: `coverage_event` is queued for semantic
review, `good_rank_event` remains blocked by a missing import environment,
`covered` remains blocked by local Lean errors, and `C_n` still needs reviewed
definition/import closure. The freshest runtime handoff is
`formalize-critic-repair:conformal_prediction_coverage:9d5dd96f`, still in
`source_theorem_exact_semantic_definition_repair` mode, and the source theorem
remains unverified until reviewed exact definitions and the proof body are
kernel checked by the prover stack.

The next live FormalizationEvaluator continuation from that handoff raised the
runtime counters to 62 kernel-verified helper/subclaim rows and 49 formal gaps,
and produced another Real-based `coverage_event` definition-only Lean candidate
that compiled locally. The subsequent Critic continuation preserved
`source_theorem_exact_semantic_definition_repair` as the top agenda and handed
off `formalize-critic-repair:conformal_prediction_coverage:c1d311e5`, while
keeping compiled `coverage_event` and semantic-review-blocked `covered`
candidates as review input only. That run exposed a smaller but important
design-level handoff bug: the full `runtime_learning_rows.jsonl` contained the
typechecked semantic-definition candidates, but the serialized pending task's
30-row bounded memory dropped them behind older adapter and routing rows. The
memory selector now pins local-Lean typechecked exact semantic-definition
candidate rows below verified adapter rows but above ordinary premise context;
a deterministic replay over the post-Critic learning rows retains 6
`coverage_event` candidate/work-order rows in the 30-row handoff. This changes
handoff visibility only: no source theorem or semantic definition is promoted
to kernel proof without reviewed exact definitions and local Lean/AXLE proof of
the intended source theorem.

The follow-up resume check found the same drift one layer earlier in the CLI:
`research-agent-runtime --resume-runtime-manifest` reloads prior
`runtime_learning_rows.jsonl` into input memory before the runtime pending-task
writer has a chance to merge same-run rows. The CLI compactor had its own
adapter/premise-oriented pinning rules, so the old serialized handoff would
still starve compiled `coverage_event` candidates during actual resume. The
CLI now pins local-Lean typechecked exact semantic-definition candidates with
the same priority boundary as the runtime writer and preserves the
`semantic_definition_kernel_verified=false` field through compaction. A live
resume from
`runs/main_worker_exact_semantic_definition_post_authoring_critic_live/research_agent_runtime_manifest.json`
advanced the Formalizer run to 64 kernel-verified helper/subclaim rows and 50
formal gaps while carrying 7 exact semantic-definition memory rows into the
pending Critic task. The subsequent Critic continuation handed back
`formalize-critic-repair:conformal_prediction_coverage:4b94cd47` with
`source_theorem_exact_semantic_definition_repair_feedback`,
`SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY`, and compiled `coverage_event`
review rows still visible. The exact source-theorem proof body remains
unverified; this was routing repair, not proof promotion.

The next Formalizer continuation from
`formalize-critic-repair:conformal_prediction_coverage:4b94cd47` advanced the
runtime counters to 66 kernel-verified helper/subclaim rows and 51 formal gaps,
but exposed another control-plane evidence-boundary bug. Closure review
packets include a nested
`source_theorem_exact_semantic_definition_typechecked_candidate` object for
each placeholder, even when that object is only a shell with
`local_definition_lean_compiled=false` and no candidate artifact or typecheck
status. The ProofEngineer bridge treated the mere presence of that shell as a
real typechecked candidate, so `good_rank_event` was routed to
`review_typechecked_exact_definition_candidate` despite having no candidate to
review. The bridge now requires concrete candidate evidence: a definitions-only
or full candidate artifact path, `local_definition_lean_compiled=true`, or a
typechecked/semantic-review-required status. A patched integrated replay in
`runs/main_worker_exact_semantic_definition_4b94_formalizer_bridge_strategy_fix_live`
routes `good_rank_event` to `author_reviewed_definition_from_contract`, `C_n`
to import/declaration review, and only `coverage_event`/`covered` to candidate
review. Source theorem and semantic-definition kernel flags remain false, and
the exact proof-body gate remains `SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY`.

The subsequent Critic continuation from
`critic:conformal_prediction_coverage:cc7271e4` preserved that proof boundary
and handed back a Formalizer repair task, but exposed a memory-retention drift
in the central AgentRuntime handoff. The pending task still carried
`source_theorem_exact_semantic_definition_repair_required=true`, yet the
bounded 30-row `runtime_learning_memory` was dominated by duplicate adapter and
premise support rows. Direct, still-untyped repair routes for
`good_rank_event` and `C_n` could be crowded out or represented only through
broad adapter context, even though `SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY`
made those exact semantic definitions the current proof blocker. The runtime
and CLI memory selectors now pin exact semantic-definition repair routes by
placeholder even when they are not typechecked candidates, and the same-run
pending-task writer dedupes pinned rows by semantic key before merging latest
rows. A patched live replay in
`runs/main_worker_exact_semantic_definition_cc7271_critic_memory_pin_fix_live`
hands off `formalize-critic-repair:conformal_prediction_coverage:554b672a`
with direct memory rows for `good_rank_event`, `C_n`, `coverage_event`, and
`covered`. This is still orchestration memory only: the source theorem and
semantic-definition kernel flags remain false, and the proof-body gate remains
`SEMANTIC_REVIEW_REQUIRED_BEFORE_PROOF_BODY`.

The next live Formalizer continuation from
`formalize-critic-repair:conformal_prediction_coverage:554b672a` showed the
same design concern in the execution router rather than memory. Once a
definition-only candidate existed for `good_rank_event`, local Lean reported an
import/environment failure, but the Lean repair executor treated that as
environment feedback only. It did not also send the failed definition candidate
back to the Claude/ProofEngineer authoring loop with diagnostics, so the next
authoring budget was spent on the already semantic-review-blocked
`coverage_event` and `covered` rows. The executor now treats failed
definition-only candidates as typed exact semantic-definition authoring repair
work items for local Lean failures, missing candidate artifacts, and import or
dependency environment failures. The authoring task and prompt carry the
definition-only artifact path, failure classification, local Lean diagnostics,
and recommended next action; environment repair still remains a separate
non-proof work item. A deterministic replay over the 554b bridge tasks now
routes `good_rank_event`, `coverage_event`, and `covered` to authoring repair,
and routes `good_rank_event` plus `C_n` to Lean environment/import repair. This
is the intended design split: core runtime enforces evidence boundaries and
typed routing, while the LLM/prover workers perform the actual Lean repair.
Source theorem and semantic-definition kernel flags remain false.

The patched live rerun
`runs/main_worker_exact_semantic_definition_554b_provenance_patched_formalizer_live`
confirmed the integrated behavior with Claude/Sonnet authoring enabled. The
authoring worker made 3 live calls for `good_rank_event`, `coverage_event`, and
`covered`. The materialized Lean repair executor checked all 3 definition-only
candidates: `good_rank_event` and `coverage_event` compiled and now require
semantic faithfulness review, while `covered` failed on a Lean import
environment blocker and was routed back to exact semantic-definition authoring
repair plus environment repair. A second control-plane loss showed up in this
run: authoring provenance (`authoring_mode`, source execution status, and
candidate repair feedback) survived the prompt but was dropped from candidate
packets, materialization rows, Lean repair results, review packets, and
environment preflight learning rows. Those artifacts now preserve the
provenance as non-proof metadata. Deterministic replay of the materialized
repair tasks confirms the final review packets for `good_rank_event` and
`coverage_event`, the follow-up authoring repair for `covered`, and the
environment preflight learning row all carry the source repair mode and
diagnostics context. This is still not semantic review and not source theorem
proof: exact proof-body execution remains blocked by
`source_theorem_semantic_alignment_unreviewed`.

The next Critic continuation
`runs/main_worker_design_policy_patch_critic_after_554b_provenance_live`
confirmed the review-ready candidates were generated, but exposed one more
control-plane handoff leak: artifact-distinct typechecked exact
semantic-definition candidates for the same placeholder were deduped as the
same memory row, and the Formalizer summary could therefore surface stale
pinned candidates before the current run's artifacts. The runtime summary now
dedupes exact semantic-definition candidates by concrete artifact/status
evidence and prioritizes direct review-required local-Lean-checked candidates
over generic older repair rows, while keeping compiled import candidates first
in diagnostic lanes. A deterministic recomputation over the pending task now
surfaces the current `coverage_event` and `good_rank_event` definition-only
artifacts from that run, and `tests/test_research_agent_runtime.py` passes
346/346. This is not a conformal theorem shortcut: it is generic evidence
handoff hygiene so Claude/ProofEngineer reviews the actual current Lean
candidate instead of rediscovering or repairing stale artifacts.

The follow-up Formalizer continuation
`runs/main_worker_current_semantic_candidate_handoff_formalizer_live` exercised
that handoff. It generated fresh current-run review packets for
`good_rank_event` and `coverage_event`, advanced the local Lean helper/subclaim
count to 70, and handed back `critic:conformal_prediction_coverage:538650a9`.
It also exposed the same bug at a second boundary: the Formalizer repair
work-order extractor iterated every historical formalization manifest on the
blackboard, so stale exact semantic-definition work orders for the same
target/placeholder could coexist with the current repair target under different
work-order ids. The extractor now collapses repair work orders by semantic
target plus placeholder, chooses the strongest/current candidate artifact by
evidence priority, and preserves all source formalization manifest ids for
traceability. A deterministic replay over the live result now returns four
work orders and selects the current `coverage_event` and `good_rank_event`
artifacts. This remains orchestration memory only: these definition-only
candidates are review inputs, not semantic-definition proof or source theorem
proof.

The next Critic/Formalizer continuation exposed a subtler version of the same
design issue. The bounded pending-task memory could retain only a subset of the
exact semantic-definition work orders, while the full exported queue already
contained the complete frontier: `good_rank_event`, `C_n`, `coverage_event`,
and `covered`. Critic feedback also compacted exact semantic-definition
diagnostics without consistently carrying `placeholder_symbol`, so the next
Formalizer could receive a generic target-level repair note instead of a
machine-actionable placeholder-level queue. The runtime now attaches
`runtime_exact_semantic_definition_work_order_feedback` to pending tasks from
the full exact semantic-definition work-order queue, and merges those rows back
into Critic's exact semantic-definition repair feedback. The enriched live
Critic run
`runs/main_worker_resume_pending_critic_full_exact_queue_feedback_live` hands
off all four placeholders with non-proof statuses. The follow-up Formalizer run
`runs/main_worker_formalizer_after_full_exact_queue_feedback_live` consumed
that queue, advanced support subclaims from 70 to 72, produced review packets
for `good_rank_event`, `coverage_event`, and `covered`, and kept `C_n` as the
named Lakefile/import-environment blocker. This is still not source theorem
proof: it is a queue-integrity fix so Claude/ProofEngineer works from the full
runtime frontier rather than a lossy memory sample.

The follow-up Critic and Formalizer continuations tightened the same queue into
typed prover/RAG work instead of generic prose. The patched Critic resume
`runs/main_worker_resume_critic_placeholder_resource_requests_live` now attaches
four `critic_source_theorem_exact_semantic_definition_repair_feedback` blocker
requests, one each for `good_rank_event`, `C_n`, `coverage_event`, and `covered`,
with placeholder-specific fingerprints and
`FORMAL_BLOCKER_RESOURCE_REQUEST_NOT_PROOF_EVIDENCE`. The Formalizer resume
`runs/main_worker_formalizer_after_placeholder_resource_requests_live` consumed
those requests, kept support subclaims at 72 and formal gaps at 54, and handed
off `formalize-repair:conformal_prediction_coverage:c297d6c1` after the local
packet validator rejected a non-theorem `lean_statement_sketch`. The repair
feedback now explicitly tells the Formalizer to put only theorem/lemma
declarations in executable Lean sketches, or to use an empty source-theorem
`FORMAL_GAP` plus typed blockers. This remains a design/contract repair only:
review packets, blocker requests, and validation feedback are not proof of
`split_conformal_finite_sample_coverage`.

The next live resume validated the intended contract shape. Runtime feedback
normalization now refreshes validator repair directives from carried
`validation_errors`, including older pending tasks created before the current
directive logic existed. The continuation
`runs/main_worker_formalizer_after_validation_directive_refresh_live` moved out
of the Formalizer packet-validation loop and handed off to
`critic:conformal_prediction_coverage:de008099`, with 74 kernel-verified
support subclaims, 55 formal gaps, and scorecard 44/49 not ready. The source
theorem remained an empty `FORMAL_GAP`; the executable helper was marked
`source_theorem_target_known=false`; and the single locally compiled
`hGoodRankImpliesCovered` source-to-bridge derivation was recorded only as
premise-derivation evidence. The remaining frontier is semantic review and
Lean environment repair for exact definitions, not another opportunity to
promote helper Lean or retrieval hits as source-theorem proof.

The next Critic handoff showed why typed artifacts matter more than longer
instructions. Critic preserved the four exact-semantic blocker requests, but
the placeholder/gate/queue metadata lived only inside the human-readable
`blocker` string. The runtime now emits `placeholder_symbol`,
`proof_body_gate_status`, `runtime_queue_status`, and `request_fingerprint`
directly on each exact-semantic blocker request, and also carries compact
gate/status summaries on the merged exact-semantic repair feedback. The patched
Critic replay
`runs/main_worker_critic_after_exact_request_metadata_v2_live` verifies those
fields for `good_rank_event`, `C_n`, `coverage_event`, and `covered`. The
Formalizer consumption run
`runs/main_worker_formalizer_after_exact_request_metadata_live` increased
support subclaims to 76 but still kept the source theorem as a non-proof
`FORMAL_GAP`, with semantic review and the `C_n` Lake/import repair as the
active frontier.
