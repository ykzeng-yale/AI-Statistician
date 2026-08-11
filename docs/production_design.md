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

The Architect creates the initial plan, resolves genuine conflicts between
workspaces, chooses a new route when a lineage budget is exhausted, and decides
when to stop. Routine syntax, ABI, compiler, simulation, or Lean failures do not
return to the Architect. They stay with the model that owns the source.

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
typed graph.

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
discovery still uses a large structured packet today; that is explicit technical
debt, not the target design.

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
Targeted theory revision now uses this model-owned workspace pattern with
read-on-demand parent and reviewer artifacts, typed complete replacements, and
same-session validator feedback. Initial discovery is not yet persistent, and the
system must not claim full theory-development capability until fresh evaluations
exercise both discovery and revision across unrelated tasks.

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
their raw stdout, stderr, request, and exact source hash to the same coding model.

Independent semantic review checks whether the implementation represents the
accepted theory artifact. Passing execution is not statistical validity, and
passing simulation is not theorem proof.

## Empirical protocol

Confirmatory metrics are proposed and independently reviewed before confirmatory
results are visible. Their identities and numeric authority are frozen for that
candidate. A failed result cannot mutate its own gate.

The minimal control pattern is:

```text
Architect authors one complete protocol
  -> independent reviewer reports source-grounded findings
  -> author may revise the complete pre-result protocol once within budget
  -> Architect resolves any remaining cross-workspace conflict
  -> execution evaluates the frozen protocol
```

The reviewer reports defects and evidence; it does not choose a `repair_scope` or
route tasks. This metric layer is still larger than the canonical design and is
the next consolidation target. Independent review and pre-result freezing remain
required while ownership routers and duplicate finding taxonomies are removed.

## Lean formalization workspace

Formalizer/ProofEngineer owns one complete standalone Lean candidate at a time.
The workspace exposes task-bound retrieval, declaration inspection, current goal
and local context, Lean LSP/MCP state, and exact compiler output. The same model
chooses each action and complete source replacement. Runtime does not inject an
import, theorem statement, tactic, or proof-body fragment.

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

As of 2026-08-11, the v323 authoritative development panel remains 0/2 exact
source-theorem closures with a 9/16 capability scorecard. It exposed a root-lineage
error: dependent formal and empirical work continued after a rejected theory
revision failed. The canonical runtime now stops that dependency chain, and a
focused exact-Haiku replay accepted the corrected flat typed workspace protocol in
two turns. Those corrections are not fresh panel evidence. The held-out panel
remains sealed and the system is not yet fully end to end.

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
- `lean_candidate_revision_tool_loop.py`: direct Lean search/edit/check loop.
- `lean_kernel_promotion.py`: exact artifact and kernel evidence gate.
- `formal_source_index.py` and scoped retrievers: declaration-level formal RAG.
- `structured_output_retry.py`: same-model schema retry transport.
- `research_agent_runtime_audit.py`: integrated evidence audit, not a scheduler.

The immediate priorities are to exercise the corrected theory lineage in a fresh
exact-Haiku development panel, move initial substantive theory authoring into the
artifact workspace where live ablation supports it, consolidate the metric
protocol control plane, and improve direct Python/R and Lean loops. No new
subsystem should be added unless it removes more control paths than it introduces
or represents a genuinely independent authority boundary.

## Basic checks

```bash
python3 -m ai_statistician.cli doctor --out runs/doctor
python3 -m pytest -q
python3 -m ai_statistician.cli research-agent-runtime --help
```
