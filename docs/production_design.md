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
  -> model chooses a tool or writes complete source
  -> isolated environment executes the exact source
  -> raw observation returns to the same model
  -> model revises the complete source
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

`structured_output_retry.py` is transport, not a semantic repair system. Its
canonical use is limited to compact control and handoff envelopes. Substantive
theory, Python, R, and Lean artifacts belong in model-owned workspaces where the
same model receives raw validator or environment observations and submits complete
artifact replacements. Runtime never fills in substantive fields. Initial theory
discovery and targeted revision use that workspace today. The bounded estimator-
interface handoff still uses structured output; it remains acceptable only while
it is small, visible, and not losing source-owner feedback.

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
Initial discovery and targeted revision now share this model-owned workspace
pattern. Initial discovery reads one content-addressed question/Architect/RAG/
contract context and may author coherent artifact groups across bounded
submissions; revision reads the exact parent and reviewer artifacts on demand.
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

The runtime may require a small general ABI, such as an exported estimator entry
point, because an executor needs a callable boundary. It may not encode a specific
statistical answer in that ABI. Unit-test and simulation-consumer failures return
raw stdout, stderr, current metric failures, and bounded callback samples when a
binding fails. The complete execution artifact is persisted once. After a binding
passes, repeated callback samples and stale execution turns leave model context;
the same source owner receives the current complete source and latest observation.
A byte-identical source submission is a tool no-op, never a runtime source edit.

For live providers with native client tools, the structured proposal carries only
artifact identity and immutable bindings. Source is authored afterward in the same
model-owned workspace. One terminal `submit_scientific_source` tool stores and
immediately executes each complete Python or R candidate unchanged. A failed raw
observation returns to that owner on its next bounded turn; no repair worker or
content patch runs between them. Planning-time estimator IDs remain frozen.
Structured-source packets remain only a replay/static-provider fallback.

Independent semantic review checks whether the implementation represents the
accepted theory artifact. Passing execution is not statistical validity, and
passing simulation is not theorem proof.

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

Formalizer/ProofEngineer owns one complete standalone Lean candidate at a time.
The workspace exposes task-bound retrieval, declaration inspection, current goal
and local context, Lean LSP/MCP state, and exact compiler output. The same model
chooses each read action and complete source submission. Each submission is stored
unchanged and immediately checked by Lean; raw failure returns to that source owner.
Runtime does not inject an import, theorem statement, tactic, or proof-body fragment.

Each source workspace has one global turn/call budget. Runtime does not preallocate
action quotas; submission and read tools remain available and the model chooses the mix.
Declaration inspection is not a Python Lean parser or a repair policy. After the
model checks its current source, it may choose an identifier and call OpenProver's
existing `lean-lsp-mcp` `lean_declaration_file` tool against the hash-bound
project-local artifact. Lean returns the complete declaration plus bounded nearby
source context; the default is 20 adjacent lines and the transport cap is 40. The
observation remains in the same model session and is explicitly non-proof evidence.

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

As of 2026-08-11, v350 is authoritative. Every call used exact Haiku; both tasks were
`BLOCKED`, score 6/16, closure 0/2, and held-out stayed sealed. Sequential completed
initial theory without duplicate `sanity_check.conclusion`, then stopped on unresolved
review findings. Survival reached direct scientific and Lean loops, but earned neither
an accepted implementation nor a compiling target, so metrics stayed unauthorized.

v348 exposed duplicate theory output and a 28-row metric-review schema too large for
Anthropic's grammar. The duplicate field is gone. The compact reviewer replayed that
exact protocol in one structured exact-Haiku call with all 28 identities and `ACCEPT`.
This is component mechanism evidence, not simulation acceptance or proof.

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

The immediate priorities are to shrink the still-large theory preflight without
weakening independent review, improve active-project context, retrieval, and compiler
ergonomics in the direct Lean loop, and improve the scientific source model's ability
to satisfy its general executor ABI. The next run that reaches scientific coding must
also verify that one current-parent independent ACCEPT closes its lane exactly once
and unlocks the compact confirmatory metric protocol. Small parallel candidate or lemma
work may be added inside an existing workspace only after the serial loop is
stable and only with the same execution and evidence gates. Estimator-interface
authoring should move into the workspace only if fresh traces show its bounded
structured stage is a material feedback blocker. No new subsystem should be added
unless it removes more control paths than it introduces or represents a genuinely
independent authority boundary.

## Basic checks

```bash
python3 -m ai_statistician.cli doctor --out runs/doctor
python3 -m pytest -q
python3 -m ai_statistician.cli research-agent-runtime --help
```
