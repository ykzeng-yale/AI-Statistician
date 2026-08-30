# AI Statistician Production Design

## Product target

AI Statistician is an autonomous statistical theory laboratory. Given a fresh
research question or paper, it should be able to:

1. inspect prior literature, code, and data under a recorded source policy;
2. identify the estimand, assumptions, procedure, and theorem targets;
3. develop a reviewable theory argument with equation and lemma lineage;
4. implement and test scientific Python or R code;
5. run exploratory and then frozen confirmatory simulations; and
6. when task intent requests it, formalize the exact target in Lean.

Every lane stops honestly with accepted evidence, an explicit unresolved gap, or
a budget-bound failure. Formal evidence is one dimension of the product result,
not a universal prerequisite for empirical or theoretical research credit.

The product is not a collection of task-specific scripts, a theorem answer bank,
or an audit dashboard. The model performs semantic research and source authoring.
The harness supplies a reliable environment and preserves evidence boundaries.

## Canonical control graph

There is one outer `AgentRuntime` graph:

```text
Goal, source policy, and task-intent evidence contract
  -> source scout or exact replication when relevant
  -> iterative theory workspace <-> exploratory scientific workspace
  -> independent theory and source review
  -> frozen confirmatory simulation
  -> optional, advisory, or required Lean workspace
  -> final critic with a per-dimension evidence vector
```

Frozen source-only or theory-only intent starts TheoryDeveloper directly; exact
formal-only intent starts its RAG/Formalizer path. Otherwise the Architect resolves
all four evidence dimensions over the configured workspace inventory, may revise its own dimensions on genuine replans, handles cross-workspace conflicts, and decides when to stop; only operator-requested dimensions are frozen. A
workspace-continuation budget covers same-owner progress and detached author-review-author work; each contiguous collaboration segment is bounded independently, while total telemetry accumulates. Accepted evidence entering a new lane and genuine cross-artifact conflicts remain outer graph transitions. Its boundary preserves the exact pending task without asking Architect. Routine syntax, ABI,
compiler, simulation, or Lean failures stay with the model that owns the source.

Every source-owning workspace uses the same loop:

```text
model inspects objective and artifacts
  -> model chooses a tool, writes complete source, or authors an exact edit
  -> isolated environment applies or executes the exact artifact
  -> raw observation returns to the same model
  -> model revises the source or artifact
  -> pass, explicit gap, or lineage budget exhaustion
```

There is no post-runtime scheduler and no separate repair agent. A resumed run
continues from content-addressed artifacts and workspace checkpoints in the same typed
graph. Outer-budget exhaustion stores the exact pending `AgentTask`. A terminal
provider or internal-tool error seals current source-owner state and stops without
restarting the subsystem. Manifests carry only task, checkpoint, and continuation
references; explicit resume hash-verifies them. Provider-local retries repeat only the same unanswered request; substantive failures remain terminal.

The inner mechanism follows [Numina-Lean-Agent](https://github.com/project-numina/numina-lean-agent)
and [AxProverBase](https://github.com/Axiomatic-AI/ax-prover-base): a general source agent,
real feedback, optional search, and bounded context. Long work may use LeanMarathon's
blueprint/DAG; ERA search stays inside an existing executable source workspace.

The general harness audit is reproducibly pinned to [OpenAI Codex at `94cbbdda`](https://github.com/openai/codex/tree/94cbbddafc1776d5e377bca1b05932c697e82238). We adopt incremental history, stable capability-accurate tools, raw tool-error feedback, checkpoint/resume, cancellation, bounded context, explicit continuation provenance, isolated findings-first review over the exact target, authorization revision independent of compaction, and queued-message versus work-trigger semantics. Repository documents are a map and system of record, not one giant injected manual. A tool is stable within one retained session but is omitted when its underlying workspace or authority is absent; an empty search surface is not a model capability. The Claude transport retains one Anthropic SDK client across consecutive rounds while every request still binds its exact model, history, tools, metadata, immutable source/tool environment, and root authorization fingerprint. Codex's first-Node-execution Guardian fast path has no product analogue here and is not adopted. Codex Core, App Server, SDK, provider transport, and multi-agent scheduler remain outside the product because importing them would create a second runtime rather than improve statistical reasoning. The exact selective-adoption map is maintained in [`openai_codex_harness_adoption_20260825.md`](openai_codex_harness_adoption_20260825.md).
We do not embed `codex-core`, App Server, its Responses transport, shared-directory subagents, or another scheduler. Each scientific workspace is the domain session and AgentRuntime remains the sole outer graph; any sidecar requires model, tool, lineage, isolation, and resume parity and can never become authority.
Like Codex `run_turn`, a response without a tool call ends the workspace segment. The harness persists the exact response and state for explicit hash-verified continuation; it never appends a private tool instruction or resamples. Progress attributes the inner subsystem, agent, and stage separately from the outer task owner.

## Progressive commitment

The graph imposes no universal research order. TheoryDeveloper chooses early
Crossref/arXiv/GitHub queries and source handles; the harness owns hosts, source horizon,
secrets, byte bounds, checkpoint-durable exact observations, identity, hashes, and citations, but not interpretation.
Exact replication requires immutable operator-curated manifests; the retained Theory source owner runs it, audits raw observations, exact text reads, and hash-rechecked provider-native PDF/image results, then uses a narrow checkpoint only when downstream task intent excludes Theory and otherwise binds the report into an integrated Theory workspace. Visual access changes observation fidelity, not semantic authority.
For non-theory tasks that checkpoint is an immutable prerequisite to the already frozen code/simulation plan; for integrated tasks the report stays in full workspace evidence but is excluded from mathematical Theory authority. Algorithm and Simulation read the exact report on demand as replication evidence.
Runtime externalizes hash references and rejects mutation; execution and report content cannot validate theory, generated code, simulation, or proof.

Theory remains long-horizon and iterative. As soon as the estimand, DGP,
procedure interface, and a testable claim are stable enough, exploratory coding
may run in parallel and return non-confirmatory counterexamples to TheoryDeveloper.
An accepted exploratory implementation returns to the exact parent Theory workspace whenever review is still `REVISE`; evaluator authoring and confirmatory execution fail closed until theory authority is accepted.
Independent theory review establishes a stable checkpoint before frozen confirmation. A light
formalization scout may expose missing definitions in parallel, but expensive Lean proving normally
begins after the statement stabilizes unless the task explicitly selects `proof_first`.

## Responsibility boundary

The LLM owns:

- statistical definitions, assumptions, derivations, and counterexamples;
- complete Python, R, and Lean source;
- retrieval queries and selection of useful premises;
- responses to raw compiler, test, simulation, and proof-state observations;
- explicit declarations that an upstream theory or target is inconsistent.

The harness owns:

- typed task transport and content-addressed artifact references;
- isolated tool execution, resource limits, network policy, and secret isolation;
- exact source hashes, target identity, lineage budgets, and checkpoints;
- schema validation for compact control envelopes and typed tool inputs;
- independent-review separation and frozen evaluation authority;
- immutable evidence labels and Lean kernel promotion.

The harness must not own:

- runtime-authored source edits or string patches;
- theorem-family formulas, expected answers, thresholds, or aliases;
- Lean grammar fixes, tactic recipes, or model-facing compiler interpretations;
- reviewer-selected repair owners followed by deterministic routing;
- hidden bridge, queue, materializer, promotion, or fallback workflows;
- proof credit for retrieval hits, LLM judgments, pseudo-formal text, or compilation of a weaker theorem.

`structured_output_retry.py` is transport for compact control and handoff envelopes,
not semantic repair. Substantive theory, Python, R, and Lean belong in model-owned
workspaces where the same model receives raw observations and authors the next state.
Runtime may apply an exact model-authored write or edit but never chooses its content.
Theory uses direct document reads, searches, complete writes, hash-bound local edits,
and compact handoff writes in the same source-owner session.

## Theory workspace

TheoryDeveloper maintains an artifact-backed research workspace, not a JSON answer.
It owns exact definitions, assumptions and use sites, equation/lemma dependencies,
executable procedure semantics, counterexamples, gaps, and revision lineage. There is no JSON-only core-theory fallback: a provider without native client-tool turns fails closed before mathematical authoring.
Compact packets are handoff indexes. Serious theory has no per-field caps; one selector defines both the model-visible output contract and writable handoff tools for explicit task intent, so non-applicable lanes are absent rather than advertised as unusable empty artifacts.
The validator checks only typed handoff structure and formal artifacts depend on intent. Historical packets remain readable, but fresh no-intent authoring exposes only the mathematical core until the Architect binds a request-scoped plan.
Durable Markdown/LaTeX is the publishable current argument, not a transcript of false starts. An integrated replication report is a separate workspace document and cannot be the sole mathematical document in a Theory packet. Exploration stays in scratch or is explicitly delimited as `SCRATCH` or `REJECTED`; a later correction does not silently deactivate earlier active text.

Discovery and revision share exact parent and reviewer artifacts. Only model-authored
edits apply, raw validation returns to the same model, and the editor contains no
statistical rules, suggested values, or routing decisions. An explicit grounded gap
blocks the lineage without treating model judgment as proof.

Structural validity does not stop the session. Within one shared ordinary-action budget,
the model chooses its mix of reads, searches, writes, edits, and scratch work, then
continues, reports a gap, or calls `commit_theory_checkpoint`. The harness still owns
total action and turn bounds, no-progress termination, execution safety caps, and the
reserved terminal disposition. A commit proposes independent review; it is not evidence.

Supporting Theory completion compiles the validated Architect plan into the next
workspace; required review and genuine conflicts retain their authority paths.

When prior work is permitted, the same TheoryDeveloper session can inspect a frozen snapshot, Crossref record, horizon-safe exact-version arXiv HTML, or pinned public repository text without a LiteratureAgent.
An independent referee gets a separate opaque-handle session and chooses its own queries. It first reconstructs the requested load-bearing chain, then sweeps every other active assertion for contradictory definitions, explanations, assumptions, measure/type declarations, regularity, and scope.
It writes one findings-first authoritative Markdown report. Its compact envelope contains only the report hash, inspected references, disposition, actual blockers, and prior-finding statuses. Runtime checks identity and traceability, not mathematics; evaluator gold remains excluded from all live discovery.

## Scientific coding workspace

AlgorithmEngineer and SimulationEngineer own complete source and use the shared
`ScientificCodeWorkspace` loop. Python and R are first-class languages. The
scientific profile uses pinned Pyodide and WebR runtimes, with explicit package
declarations, bounded subprocesses, no inherited secrets, and no network access.
Safety comes from isolation and resource policy, not from banning the scientific
computing ecosystem.

The runtime may require a small general executor ABI, but it may not encode a
statistical answer. Syntax, safety, ABI, runtime, serialization, and consumer failures
return raw observations to the same source owner; exploratory work may also return
explicitly non-confirmatory empirical diagnostics. Execution is persisted once, stale
observations leave model context, and identical source is a tool no-op rather than a
runtime edit.

Exploratory source may start before the complete theorem program is closed once
its consumed interfaces are stable. A bound replication report is exposed through
the same hash-bound read-only document tools but never as mathematical authority.
Such runs may falsify theory but cannot satisfy frozen confirmatory gates.

For live providers with native client tools, the structured proposal carries only
artifact identity and immutable bindings; source is authored in the same model-owned
workspace. Submission and exact edits store complete Python or R source. The model
explicitly runs the current source for raw sandbox feedback, so it may batch coherent
edits before an expensive simulation. A later `commit_scientific_source` requires an
accepted hash-bound execution observation.
No repair worker, diagnostic parser, or content patch intervenes. Estimator IDs stay frozen.
Structured-source packets are historical replay only; fresh authoring fails closed without native client tools.

Confirmatory iteration stops when source is execution-valid. Realized values,
threshold verdicts, and value-derived hashes are withheld from the source model and semantic reviewer, which checks exact source, runtime arguments, frozen measurement
contract, result schema, and theory alignment. After `ACCEPT`, the immutable outcome
is released once to Architect by reference, and the same Simulation source cannot
retry. Execution is not statistical validity or theorem proof.

If Architect assigns a released outcome to AlgorithmEngineer, runtime restores the exact
parent source and frozen Simulation continuation by hash. The same coding workspace
revises complete source, receives independent review, and replays the frozen consumer
on the new cohort without a new proposal, Formalizer detour, or runtime-authored edit.

For rejected source, the reviewer asks whether editing only that source can close
all findings with theory, contract, and consumer fixed; it names no owner, route,
or edit. Sufficient findings return to the coding workspace; otherwise one compact
observation goes to Architect. Source stays in the store, outside the control task.

The reviewer owns executable-contract decomposition. Public clause IDs are navigation
addresses, not proof that a compound clause was tested. The model runs adversarial probes,
separates relevant positive, malformed, boundary, transformation, and output obligations,
and reports untested obligations. Runtime verifies execution and lineage, not semantics
or a declared coverage list. After each exact-source probe, its raw observation and the
unchanged public contract return together to the same reviewer context; this improves
attention without adding a contract parser, generated case, or deterministic verdict.

For outer-graph completion, an Algorithm or Simulation lane is complete only when
its active manifest has an independent `ACCEPT` bound to the current immutable
parents. The accepted review is the completion authority; handoff history and an
earlier source-task execution are not. A changed Theory or Algorithm parent makes
the prior review ineligible without rerouting through Architect. ACCEPT rows merge
by source workspace and immutable parent lineage so accepting Simulation cannot
erase the current Algorithm acceptance, or vice versa.

When the frozen protocol requires generated algorithm code, confirmatory
simulation can consume an estimator only through a hash-bound handoff produced by
accepted independent semantic review. A sandbox artifact that executed but was
rejected is failed evidence, not an implicit downstream dependency. Exploratory
simulation remains available when the frozen contract does not require that
handoff.

## Empirical protocol

For fresh tasks, exact executable Simulation source is the preregistration authority.
The same source-owning model authors DGPs, measurements, formulas, decision logic,
diagnostics, and replicate justification in ordinary Python or R before confirmatory
outcomes exist. Runtime validates only a generic executor ABI: one exact Boolean
`acceptance_passed` and one positive `requested_runtime_replicates` within sandbox
capacity. It contains no statistical threshold, formula, DGP, or repair rule.

There is no universal replicate count such as 100. Before outcomes are revealed,
the evaluator freezes a task-specific budget from a declared Monte Carlo standard
error, interval-width, or power target plus resource limits. Exploratory runs may
be small and adaptive but are labelled non-confirmatory. Confirmatory replication
may stop only by its predeclared precision rule, never because the observed result
crossed a desired threshold.

The minimal source-owner pattern is:

```text
Simulation owner writes and runs source on non-confirmatory diagnostics
  -> raw environment feedback returns to that same model session
  -> owner commits exact source bytes and requested confirmatory size
  -> isolated reviewer inspects those exact bytes without outcomes
  -> ACCEPT releases one exact-hash replay on the hidden cohort
  -> outcome is terminal evidence; it cannot trigger source revision
```

The reviewer may use isolated Python/R/SymPy scratch tools but must judge source semantics,
theory alignment, pre-outcome independence, and diagnostic sufficiency rather than trust
the returned Boolean. A rejection returns exact findings to the same source owner. Frozen
legacy metric packets remain reconstructable for old evidence only; they are not a fresh
authoring path. There is no prose-to-source translator, packet repair worker, result-informed
revision, or routine Architect hop.

## Lean formalization workspace

Formalization policy is `required`, `optional`, or `advisory` and scheduling is
`proof_first`, `simulation_first`, or `dual_track`. A formal gap blocks only a
required formal contract. Optional/advisory gaps are disclosed in the final
evidence vector and cannot erase accepted theory or empirical evidence. Conversely,
simulation or review can never be promoted to theorem proof. Optional/advisory
product work defaults to `simulation_first`; explicit tasks may choose another path,
while strict formal-capability evaluation remains `required` and `dual_track`.

Formalizer/ProofEngineer receives one exact theorem-goal reference already owned by
the outer research graph. Runtime resolves that upstream ID and hash only; it makes
no second LLM target-binding call. Initial authoring and later revision use the same
client-tool workspace. The model chooses retrieval, inspection, complete source plus
declaration-name submission, or a concrete task-bound formal-gap report. Each source
is stored unchanged and checked immediately; raw Lean failure returns to that model.
Runtime injects no import, theorem statement, tactic, or proof-body fragment.

One global turn/call budget covers every action. The initial message carries the
complete current source, hash, declaration, and a fresh raw Lean check. One bounded
linear model-tool transcript then retains every model action and environment
observation, which also leaves an append-only prefix for provider prompt caching.
A resumed source is rechecked in the active Lake project before the first model turn;
old checkpoint checks and search/state payloads are not copied into the new session.
Declaration inspection resolves the model-selected active-project symbol through
task-bound RAG and OpenProver's `lean-lsp-mcp`; the candidate file is only a local
fallback. All such observations remain explicitly non-proof evidence.

The stable initial/revision tool surface offers complete-source submission,
declaration/proof-state inspection, formal RAG, proof-candidate search, and a typed
formal gap. A revision gap preserves exact target provenance, clears proof-candidate
source fields, and remains non-proof. Independent review must distinguish a true
missing foundation from a fixable API or modeling error. Temporary admitted bodies or Lean `#check`/`#print` commands are diagnostic only: Lean reports elaboration and axioms, and only a complete axiom-clean source may enter review or promotion.

Every changed statement receives independent target-semantic review. When a
candidate is rejected, it cannot be handed back unchanged after temporary edits:
the same Formalizer receives a hash-bound observation and must submit changed
complete source or report a grounded formal gap. It can count as theorem evidence
only when all of the following bind to the same artifact:

- question, theorem target, declaration, project, path, and source hash;
- independent semantic acceptance of the exact statement;
- a fresh active-project Lean check of the exact bytes;
- Lean/AXLE/kernel success with no admitted proof or unsupported axiom policy.

An accepted statement is not a proof. A compiled helper lemma is not exact-target
closure. Retrieval, proof-state analogies, proof banks, and pseudo-formalization
are context only. Before promotion, a compiling artifact may record
`candidate_kernel_verified=true`, but generic `kernel_verified` and
`source_theorem_kernel_verified` remain false.

Formal RAG should align with Mathlib and Statlib declaration conventions and reuse
their active imports and definitions before introducing project-local APIs. The
canonical gitlinked `EmpericalProcessLEAN` project pins the active Lean, Mathlib,
Statlib/StatInference foundation; `lean-stat-learning-theory` and OpenProver/
CodexProver are additional resources. Search results must preserve source snapshot,
module, declaration signature, dependencies, and active-project compatibility.
See the [Statlib roadmap](https://stat-lib.github.io/roadmap.html) and
[ReProver](https://github.com/lean-dojo/reprover) for library and proof-state
search reference designs. Local Lean remains the authority.

## Artifact and observation model

Persistent control state should stay close to these primitives:

```text
TaskRef: id, owner, objective_ref, workspace_ref, budget
ArtifactRef: id, path, hash, type
Observation: tool, status, stdout_ref, stderr_ref, artifact_hash
Decision: action, target_ref, rationale_ref
```

Substantive artifacts live once in the content-addressed store. Tasks and traces
carry references, not recursive copies of prior tasks, deferred tasks, source,
and manifests. Full raw output remains available by reference; prompts receive
only the current source, active observations, target identity, and bounded
retrieval context. Semantic handoffs explicitly project current substantive
fields; provider transport, tool history, telemetry, and prior drafts stay in
the source trace rather than becoming review or retrieval inputs.

Workspace completion is parent-bound. A Theory revision retires active Algorithm,
Simulation, Formalization, accepted-review, and handoff references; historical IDs
remain audit-only. A lane counts as completed only when its recorded parent IDs
match the current immutable parents, so an old success cannot close a revised
lineage.

## Model policy

Anthropic is the current live provider. Opus is forbidden everywhere. Production
may use Haiku or Sonnet and has a hard Sonnet ceiling. Tests and evaluations use
exactly `claude-haiku-4-5-20251001` for every live model call, including retries.
They never escalate after a failure.

Tier overrides are `AI_STATISTICIAN_CLAUDE_HAIKU_MODEL` and
`AI_STATISTICIAN_CLAUDE_SONNET_MODEL`. The global
`AI_STATISTICIAN_LLM_MODEL` must not collapse cost-aware Haiku/Sonnet routing.
Every request records its resolved provider, model, tier, token use, latency, and
tool-turn count.

## Evaluation authority

Unit tests validate mechanisms, not research capability. The capability ladder reports
theory, empirical, formal, novelty, replication, and unresolved-gap dimensions; frozen
task intent decides which must pass, and no aggregate score hides a required failure.

For formal-only gold, the visible `formal_target_contract` is the exact statement. The
canonical evaluator already binds it to unchanged model source, independent semantic
acceptance, clean axiom audit, and fresh Lean kernel promotion; gold consumes that typed
closure instead of adding a hidden proof, model judge, or second verifier.

The frozen cross-family protocol remains the strict integrated formal gate and requires
exact source-theorem closure. It measures S13, not universal product completion:
optional formalization cannot weaken S13, and S13 failure cannot erase accepted
non-formal evidence.

Benchmarks progress from reproducible published results through paper-to-code, hidden
rederivation, historical rediscovery, near-frontier extension, and true open problems.
Only hidden-gold levels measure correctness; open problems report evidence and gaps,
never success from model agreement.

## Structural constraints

New work must not reintroduce:

- a second orchestration plane after `AgentRuntime` returns;
- theorem-specific bridge/executor module families;
- a repair-patch-rerun queue hierarchy;
- routine Architect hops for local environment failures;
- dependent lanes consuming an older rejected parent after its required revision fails;
- recursive artifact payloads or manifest truth-table expansion;
- task-family conditionals in canonical authoring, proving, or review code;
- proof-bank candidates as the default live proving policy;
- additional framework wrappers before the current graph is smaller.

Repository tests enforce coarse canonical-runtime, package, and design-document size budgets as regression alarms.
The preferred response is deletion and consolidation, not moving code behind a new interface.

## Current implementation map

- `agent_runtime.py`: typed scheduling, task references, artifacts, and evidence.
- `research_agent_runtime.py`: canonical outer graph and subsystem adapters.
- `scientific_code_workspace.py`: direct Python/R source-feedback loop.
- `scientific_sandbox.py`: isolated Pyodide/WebR execution.
- Lean revision and kernel-promotion modules: direct checks and exact evidence gate.
- `formal_source_index.py` and scoped retrievers: declaration-level formal RAG.
- `structured_output_retry.py`: same-model schema retry transport.
- `research_agent_runtime_audit.py`: integrated evidence audit, not a scheduler.
Priorities are model-owned counterchecks, execution timing, independent gap review, and fresh evidence; never add repair agents or theorem-specific rules.
