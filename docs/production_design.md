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

The Architect creates the initial plan, resolves independently evidenced conflicts
between workspaces, and decides when to stop. Exhausting a source-workspace budget
produces a typed block; it does not by itself trigger another routing call. Routine
syntax, ABI, compiler, simulation, or Lean failures stay with the model that owns
the source.

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
continues from content-addressed artifacts and workspace checkpoints in the same
typed graph. Outer-budget or bounded transient-provider exhaustion atomically
stores the exact pending `AgentTask`; manifests carry only its task and
continuation refs, and resume hash-verifies and restores that task without
rewriting its inputs. Substantive failures remain terminal.

The inner mechanism follows [Numina-Lean-Agent](https://github.com/project-numina/numina-lean-agent)
and [AxProverBase](https://github.com/Axiomatic-AI/ax-prover-base): a general source agent,
real feedback, optional search, and bounded context. Long work may use LeanMarathon's
blueprint/DAG; ERA search stays inside an existing executable source workspace.

## Progressive commitment

The graph imposes no universal research order. TheoryDeveloper chooses early
Crossref/GitHub queries and source handles; the harness owns hosts, source horizon,
secrets, byte bounds, commit identity, hashes, and citations, but not interpretation.
Exact replication requires immutable operator-curated source and execution manifests.
When author code writes results, declared paths are captured from a hash-audited
copy-on-write workspace; the model cannot alter source, command, environment, or output.

Theory remains long-horizon and iterative. As soon as the estimand, DGP,
procedure interface, and a testable claim are stable enough, exploratory coding
may run in parallel and return non-confirmatory counterexamples to TheoryDeveloper.
Independent theory review establishes a stable checkpoint before confirmatory
gates are frozen. A light formalization scout may expose missing definitions in
parallel, but expensive Lean proving normally begins after the statement stabilizes
unless the task explicitly selects `proof_first`.

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
executable procedure semantics, counterexamples, gaps, and revision lineage.

Compact packets are handoff indexes. Serious theory has no per-field caps; the
validator checks only typed handoff structure, while formal artifacts depend on intent.

Discovery and revision share exact parent and reviewer artifacts. Only model-authored
edits apply, raw validation returns to the same model, and the editor contains no
statistical rules, suggested values, or routing decisions. An explicit grounded gap
blocks the lineage without treating model judgment as proof.

Structural validity does not stop the session. Within one shared ordinary-action budget,
the model chooses its mix of reads, searches, writes, edits, and scratch work, then
continues, reports a gap, or calls `commit_theory_checkpoint`. The harness still owns
total action and turn bounds, no-progress termination, execution safety caps, and the
reserved terminal disposition. A commit proposes independent review; it is not evidence.

When selected task intent does not require independent theory acceptance, completion
of the supporting Theory workspace does not trigger another Architect model call.
AgentRuntime compiles the already validated, model-authored Architect plan into the
next applicable Python/R, Simulation, Lean, or Critic workspace. Required-theory
review and cross-workspace conflicts still use their existing authority paths; the
runtime does not invent a new research decision.

When prior work is permitted, the same TheoryDeveloper session can inspect a frozen
snapshot or model-selected public paper/repository text without a LiteratureAgent.
An independent referee gets a separate opaque-handle session and chooses its own
queries; search metadata is not citable, while exact reads become hash-bound refs.
Runtime persists identities, not source bodies. Sources are provenance, not proof or
referee acceptance, and evaluator gold remains excluded from all live discovery.

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
its consumed interfaces are stable. Such runs can falsify a proposed theory or
guide its revision but cannot satisfy confirmatory gates. Confirmatory source is
bound to the independently reviewed current theory and frozen protocol.

For live providers with native client tools, the structured proposal carries only
artifact identity and immutable bindings. Source is authored afterward in the same
model-owned workspace. `submit_scientific_source` stores and executes each complete Python
or R candidate unchanged, then returns the raw observation without terminating the
workspace. On a later turn, the same model may revise or explicitly finish with
`commit_scientific_source`; it cannot submit and commit before receiving the observation.
No repair worker, diagnostic parser, or content patch intervenes. Estimator IDs stay frozen.
Structured-source packets remain only a replay/static-provider fallback.

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

Confirmatory metrics are proposed and independently reviewed before confirmatory
results are visible. Their identities and numeric authority are frozen for that
candidate. A failed result cannot mutate its own gate.

There is no universal replicate count such as 100. Before outcomes are revealed,
the evaluator freezes a task-specific budget from a declared Monte Carlo standard
error, interval-width, or power target plus resource limits. Exploratory runs may
be small and adaptive but are labelled non-confirmatory. Confirmatory replication
may stop only by its predeclared precision rule, never because the observed result
crossed a desired threshold.

The minimal control pattern is:

```text
Architect authors one complete protocol
  -> independent reviewer reports source-grounded findings
  -> author may revise the complete pre-result protocol once within budget
  -> accept and freeze, or block the source workspace
  -> execution evaluates only an accepted frozen protocol
```

Metric row limits are execution/review budgets, not statistical rules. The reviewer
supplies a theory-consistent positive control that the frozen evaluator executes.
Runtime reports that observation; models still own protocol semantics and revisions.
There is no whole-packet repair worker or runtime-authored statistical transformation.

A rejected `metric_contract_review` returns the exact findings to the same metric
author inside that bounded operation. If the revised candidate remains rejected,
the operation blocks with its full lineage; it does not ask Architect to reinterpret
a protocol defect as a TheoryDeveloper task. A later outer-plan change requires a
separately evidenced cross-workspace inconsistency.

A rejected theory preflight returns exact observations to the parent-bound theory
workspace. The reviewer may query task-bound literature or formal RAG, and every
cited source is snapshot-verified. Prior findings remain immutable records but may
be resolved or retracted by the independent model using current evidence; runtime
only validates lineage.

The independent reviewer may author an isolated Python/R/SymPy scratch countercheck and interpret its raw result in the existing tool loop.
When useful it targets the disputed intermediate claim; final-output agreement cannot establish that derivation. Runtime stores hash-bound lineage only: exploratory, never confirmatory/proof, with no added reviewer, vote, repair worker, or route.

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
configured source graph includes Mathlib, Statlib/StatInference,
`lean-stat-learning-theory`, the Statlib-founded `EmpericalProcessLEAN`, and
OpenProver/CodexProver resources. Search results must preserve source snapshot,
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

Unit tests validate mechanisms, not research capability. Product research uses
`benchmarks/research_capability_ladder_20260814.json` and reports separate theory,
empirical, formal, novelty, replication, and unresolved-gap dimensions. A task
passes only the dimensions required by its frozen intent; no aggregate score hides
a required failure.

The frozen `autonomous_cross_family_e2e_protocol_20260713.json` remains the strict
integrated formal-capability gate. Its development and held-out tasks require exact
source-theorem kernel closure and stay sealed under their existing rules. That gate
measures S13 formal integration, not universal product completion. Optional product
formalization does not weaken S13, and S13 failure does not invalidate independently
accepted non-formal research evidence.

Benchmark progression starts with reproducible published results and immutable
code/data snapshots, then paper-to-code reproduction, hidden known-theory
rederivation, historical rediscovery, near-frontier extension, and finally true
open problems. Only levels with hidden gold can measure correctness. Open-problem
runs report evidence and remaining gaps, never “success” from model agreement.

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
- `lean_candidate_revision_tool_loop.py`: direct Lean read/submit-and-check loop.
- `lean_kernel_promotion.py`: exact artifact and kernel evidence gate.
- `formal_source_index.py` and scoped retrievers: declaration-level formal RAG.
- `structured_output_retry.py`: same-model schema retry transport.
- `research_agent_runtime_audit.py`: integrated evidence audit, not a scheduler.

Priorities are model-owned counterchecks, execution timing, independent gap review, and fresh evidence; never add repair agents or theorem-specific rules.
