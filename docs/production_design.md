# AI Statistician Production Design

## Product target

AI Statistician is an autonomous statistical theory laboratory. Given a fresh
research question or paper, it should be able to:

1. identify the estimand, assumptions, procedure, and theorem targets;
2. derive a rigorous theory argument with explicit equation and lemma lineage;
3. implement and test scientific Python or R code;
4. design and run simulations under a protocol frozen before confirmatory results;
5. formalize the exact target in Lean using task-bound retrieval and live Lean state;
6. revise its own artifacts from raw environment feedback and stop only with an
   honest result: accepted evidence, an explicit gap, or a budget-bound failure.

The product is not a collection of task-specific scripts, a theorem answer bank,
or an audit dashboard. The model performs semantic research and source authoring.
The harness supplies a reliable environment and preserves evidence boundaries.

## Canonical control graph

There is one outer `AgentRuntime` graph:

```text
Goal and plan
  -> Theory workspace
  -> Scientific coding and simulation workspace
  -> Independent semantic review
  -> Lean formalization workspace
  -> Final critic and kernel gate
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

This deliberately adopts the minimal mechanism shared by
[Numina-Lean-Agent](https://github.com/project-numina/numina-lean-agent) and
[AxProverBase](https://github.com/Axiomatic-AI/ax-prover-base): a general source
agent, real environment feedback, optional search, and bounded context. For
long-horizon formalization, the useful idea from
[LeanMarathon](https://github.com/YuanheZ/LeanMarathon) is a durable blueprint and
lemma DAG with CI gates; it is an artifact model, not a reason to duplicate its
agent hierarchy inside this runtime. Scientific candidate search may later adopt
the small `generate -> execute -> score` interface from
[ERA](https://github.com/google-research/era), but only within an existing source
workspace.

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
- proof credit for retrieval hits, LLM judgments, pseudo-formal text, or compilation
  of a weaker theorem.

`structured_output_retry.py` is transport, not a semantic repair system. It is
limited to compact control and handoff envelopes. Substantive theory, Python, R,
and Lean artifacts belong in model-owned workspaces where the same model receives
raw observations and authors the next artifact state. Runtime may apply a standard
model-authored edit, but never chooses it or fills content. Initial discovery and
revision use one atomic RFC 6902 editor. The bounded estimator-interface handoff
remains acceptable only while small, visible, and preserving owner feedback.

## Theory workspace

The TheoryDeveloper must maintain an artifact-backed research workspace rather
than treating a small JSON packet as the theory itself. Its durable products are:

- exact definitions and notation;
- an assumption ledger with necessity and use sites;
- an equation derivation and lemma dependency graph;
- estimand, estimator/test/procedure, and executable data-generating semantics;
- counterexamples, failure regimes, and unresolved mathematical gaps;
- revision links from simulation, semantic review, and formalization observations.

Compact structured packets are handoff indexes into this workspace. Fixed numbers
of equations, lemmas, or characters are transport limits, never quality criteria.
The workspace validator requires nonempty typed derivation, equation, assumption,
and sanity-check structures plus a primary estimator, theorem target, and
formalization request; it does not prescribe how many rows constitute a rigorous
argument. Supporting lemma, critic-finding, and next-action lists may remain empty
when the model has no justified item. Independent theory preflight and the final
Critic, rather than schema cardinality, judge mathematical sufficiency.
Initial discovery and revision share this model-owned workspace. Discovery reads
one content-addressed question/Architect/RAG/contract context; revision reads exact
parent and reviewer artifacts on demand. Both apply only model-authored standard
JSON edits. The editor has no statistical rules, suggested values, or routing role.
Each structurally valid partial write is retained even when the combined workspace
still fails validation. The tool reports that write as accepted, returns the raw
validation errors, and lets the same model submit only the remaining or revised
artifacts. The last invalid write stops immediately with a model-owned checkpoint;
it does not spend later turns calling an exhausted tool. Capability audit requires
this direct evidence, but the system must not claim full theory-
development capability until fresh cross-family evaluations exercise both paths.

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

For live providers with native client tools, the structured proposal carries only
artifact identity and immutable bindings. Source is authored afterward in the same
model-owned workspace. One terminal `submit_scientific_source` tool stores and
immediately executes each complete Python or R candidate unchanged. A failed raw
observation returns to that owner on its next bounded turn; no repair worker or
content patch runs between them. Planning-time estimator IDs remain frozen.
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

The minimal control pattern is:

```text
Architect authors one complete protocol
  -> independent reviewer reports source-grounded findings
  -> author may revise the complete pre-result protocol once within budget
  -> accept and freeze, or block the source workspace
  -> execution evaluates only an accepted frozen protocol
```

New protocols carry at most eight required metric rows. This is an execution and
review budget, not a statistical rule: repeated scenarios use vector measurements
and explicit aggregation. A frozen historical protocol keeps its exact row set.

The reviewer reports defects and evidence; it does not choose a `repair_scope` or
route tasks. Authoring and independent review remain one bounded Architect protocol
operation with separate model contexts and visible timing substages. They should not
be promoted into two additional outer tasks merely for telemetry. Independent review
and pre-result freezing remain required while ownership routers and duplicate finding
taxonomies are removed.

The reviewer returns one judgment per immutable requirement, one portfolio judgment,
prior-finding decisions, and new findings. Runtime binds exact identities, checks
coverage and lineage, and derives the fail-closed verdict; the model owns every
rationale. There is no matrix checklist or whole-packet regeneration retry.

A rejected `metric_contract_review` returns the exact findings to the same metric
author inside that bounded operation. If the revised candidate remains rejected,
the operation blocks with its full lineage; it does not ask Architect to reinterpret
a protocol defect as a TheoryDeveloper task. A later outer-plan change requires a
separately evidenced cross-workspace inconsistency.

A rejected `theory_execution_preflight` returns its observations directly to the
exact parent-bound TheoryDeveloper workspace. This is a fixed stage-ownership
edge, not a reviewer-selected owner or an Architect model route. The reviewer
inspects exact theory anchors first and may query task-bound RAG when it needs
additional context; search and external citations are not mandatory. Every cited
external handle is runtime-verified against the returned source snapshot, while
uncited search results do not force unrelated findings to carry citations.
Independent queries may share one client-tool turn.

Prior preflight findings are immutable identities, not irreversible verdicts. On
the next current-parent review, the independent model may mark a prior finding
`RESOLVED_BY_CURRENT_THEORY` when the source changed, or
`RETRACTED_BY_CURRENT_EVIDENCE` when current anchors show the prior claim is
contradicted, outside the admitted DGP or requested measurements, or only a
downstream implementation/proof obligation. Both require a model-authored rationale
and current evidence refs. Runtime never chooses a retraction; it only validates
the binding and removes closed rows from the active ledger.

## Lean formalization workspace

Formalizer/ProofEngineer receives one exact theorem-goal reference already owned by
the outer research graph. Runtime resolves that upstream ID and hash only; it makes
no second LLM target-binding call. Initial authoring and later revision use the same
client-tool workspace. The model chooses retrieval, inspection, complete source plus
declaration-name submission, or a concrete task-bound formal-gap report. Each source
is stored unchanged and checked immediately; raw Lean failure returns to that model.
Runtime injects no import, theorem statement, tactic, or proof-body fragment.

One global turn/call budget covers every action. A short rolling transcript retains
recent retrieval and inspection results; one authoritative snapshot carries the
complete current source, hash, declaration, latest raw Lean check, usage, and budget.
A resumed source is rechecked in the active Lake project before the first model turn.
Old checkpoint checks and search/state payloads are not permanent prompt fields.
Declaration inspection resolves the model-selected active-project symbol through
task-bound RAG and OpenProver's `lean-lsp-mcp`; the candidate file is only a local
fallback. All such observations remain explicitly non-proof evidence.

The stable initial/revision tool surface offers complete-source submission,
declaration/proof-state inspection, formal RAG, proof-candidate search, and a typed
formal gap. A revision gap preserves exact target provenance, clears proof-candidate
source fields, and remains non-proof. Independent review must distinguish a true
missing foundation from a fixable API or modeling error.

Every changed statement receives independent target-semantic review. A candidate
can count as theorem evidence only when all of the following bind to the same
artifact:

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
retrieval context.

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

Unit tests validate mechanisms but do not establish research capability. The
frozen cross-family protocol is the product gate. Each fresh task must show the
same-run lineage:

```text
plan -> theory -> model-authored code -> isolated execution
     -> independent review -> frozen simulation protocol -> fresh results
     -> exact formal target -> task-bound RAG and Lean feedback
     -> exact source-theorem kernel closure -> final critic
```

Development tasks may drive shared interface and harness fixes. Held-out tasks
remain sealed until the development gate passes, and their outcomes may not be
used to add theorem-family rules. A capability scorecard, support lemma count, or
audit percentage cannot substitute for exact closure on each task.

As of 2026-08-13, v390 is the latest fresh integrated panel. Exact Haiku scored
6/16, ended with two `BLOCKED` tasks, and closed 0/2 exact source theorems. Both
tasks executed Algorithm code but exhausted Theory revision/preflight before
Formalizer; this is an upstream contract failure, not Lean evidence.

Direct v391-v394 ablations reuse one exact v389 target. Four retained tool turns
reduced input from 435185 tokens in v391 to 291767 in v393 while preserving eight
source updates; a two-turn test regressed to zero updates and was reverted. At
`1fdb1e6a`, v394 made five updates and six Lean checks, then reported a typed gap
without proof credit. OpenProver search remained unused and the claimed primitives
remain unreviewed. This is component evidence only. Held-out tasks remain sealed;
`all_ok=true` cannot override 0/2 kernel closure.

## Structural constraints

New work must not reintroduce:

- a second orchestration plane after `AgentRuntime` returns;
- theorem-specific bridge/executor module families;
- a repair-patch-rerun queue hierarchy;
- routine Architect hops for local environment failures;
- dependent lanes consuming an older rejected parent after its required revision
  fails;
- recursive artifact payloads or manifest truth-table expansion;
- task-family conditionals in canonical authoring, proving, or review code;
- proof-bank candidates as the default live proving policy;
- additional framework wrappers before the current graph is smaller.

Repository tests enforce coarse size budgets for the canonical runtime, package,
and design document. Those budgets are regression alarms, not architecture goals;
the preferred response is deletion and consolidation, not moving code behind a
new interface.

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

Immediate priorities are model-owned theory counterchecks, execution timing, formal-gap review,
and integrated v395 evidence. New work must simplify tools, never add repair agents or theorem-specific rules.
