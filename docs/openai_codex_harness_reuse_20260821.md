# OpenAI Codex Harness Reuse Audit

## Upstream identity

- Repository: `https://github.com/openai/codex`
- Audited branch: `main`
- Audited commit: `45a3edc02a59d845eba30794796c44e5f2377408`
- License: Apache-2.0
- Read-only checkout: `/Users/yukangzengcmac/.codex/external/openai-codex-45a3edc0`
- License SHA-256: `d17f227e4df5da1600391338865ce0f3055211760a36688f816941d58232d8dc`

The audit is commit-bound. A later Codex release is a different mechanism
snapshot and must not silently replace this identity.

The prior audit was pinned at `e482cc66aeeedcb9f333a1f5a0a554eb5aea4b36`.
The incremental recheck to `45a3edc0` found no byte changes in the six core
files below. The intervening relevant changes preserve TUI event order, enforce
remote-environment network policy, and retain MCP compatibility; they reinforce
stable observation ordering and environment-owned policy but do not justify a
second scheduler or provider path in AI-Statistician.

## What Codex actually contributes

Codex has a small conceptual kernel even though its production repository is
large:

1. A thread is durable conversation state, a turn is one user-to-agent run,
   and an item is one persisted message, tool call, command, or file edit.
2. Inside a turn, the same model repeatedly selects tools and receives their
   exact outputs. A final assistant response ends the turn.
3. Tool routing separates model-actionable failures from fatal runtime
   failures. Ordinary tool failures become model observations; a fatal harness
   failure aborts instead of asking the model to repair the harness.
4. The tool runtime snapshots the advertised tool surface for a sampling step,
   preserves output order, supports concurrent safe calls, serializes unsafe
   calls, and propagates cancellation.
5. Multi-agent V2 creates isolated child threads. A child can inherit no
   turns, the last N turns, or all turns. Queue-only messages do not start a
   new child turn; follow-up tasks do. Waiting is mailbox-driven rather than
   busy polling.
6. The app-server exposes thread, turn, and item events over a bidirectional
   protocol and can attach dynamic tools, sandbox policy, and workspace roots.

Primary inspected files and their SHA-256 identities:

| Upstream file | Mechanism | SHA-256 |
| --- | --- | --- |
| `codex-rs/core/src/session/turn.rs` | same-session model/tool continuation | `dfaf8eed97c12916fb8d7c454c455bb6f6f4eb3c5fe8e5d2636e22f7a3a7263b` |
| `codex-rs/core/src/tools/parallel.rs` | typed dispatch, ordering, cancellation, fatal boundary | `48380e25abaf9c52e7a5de9cecf82cc4ddb84197683f73a11719de3b78c90e5a` |
| `codex-rs/core/src/session/multi_agents.rs` | context-selective child agents and mailbox guidance | `44197c5fb2b32ec158c5488b419141e9e626614c64d524b6a2a90500a272f53f` |
| `codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs` | zero/N/all-turn fork policy | `3bb8b56b430c095bea3f7e1ccebb9a73d2c889786a281942bb0cd2ca676a1300` |
| `codex-rs/app-server/README.md` | thread/turn/item protocol and dynamic tools | `6da52c64da3e6a7d1f6dcbc636d22aabc5d0935cb4f4f07951501236f84e5b98` |
| `codex-rs/model-provider-info/src/lib.rs` | provider transport contract | `c3aa8df9ffd0ddc8010c7c2057b85f539ae5de92873549f2958e53149cb37dd4` |

## Fit with AI-Statistician

AI-Statistician already has the correct two scales of control:

- `AgentRuntime` is the outer scientific evidence graph. It owns task intent,
  artifact identity, independent review, routing across research domains, and
  final evidence status.
- `client_tool_loop` is the inner coding-agent loop. The source-owning model
  selects tools, receives raw observations, and revises Theory Markdown,
  Python/R source, simulation source, or Lean source in the same context.

Codex therefore validates the inner-loop direction; it does not justify
placing another Codex thread manager around `AgentRuntime`.

### Adopted now

1. Unknown tool-runtime exceptions fail immediately through a secret-free
   `ClientToolRuntimeError`. They are not converted into a fake observation
   that asks TheoryDeveloper, AlgorithmEngineer, Simulator, or Formalizer to
   repair runtime code. Only declared `ClientToolInputError` observations are
   returned to the model.
2. Read-heavy Theory and Lean workspaces permit multiple independent model
   tool calls in one provider turn. The model may batch independent reads,
   searches, or inspections; runtime still processes side effects in stable
   order, and terminal actions must remain last.
3. Scientific source execution stays observation-sequential. A revised Python
   or R program must see the prior execution result before another candidate
   is generated; parallel speculative submissions would spend execution
   evidence without feedback.
4. Theory author stopping is model-owned. The complete document write and its
   exact tool result already remain in the same client-tool session, so runtime
   no longer forces the author to reread every line at the final document hash
   before requesting independent review. Model-chosen reads remain recorded,
   while the isolated referee still has to inspect every authoritative document
   under its separate hash-bound coverage gate.
5. Python and R source workspaces now survive an exhausted inner tool-loop
   segment without regenerating their planning envelope. The next outer-runtime
   step returns the exact content-addressed source and its raw execution
   observation to the same AlgorithmEngineer or SimulationEngineer. Accepted
   sibling sources are referenced without re-execution, and a continuation is
   authorized only after a new sandbox check. A stale checkpoint, changed hash,
   overlapping continuation, or no-progress lineage fails closed before a model
   call; ordinary source continuation never routes through Architect.
6. Referee-driven TheoryDeveloper revision no longer has a separate one- or
   two-round cap. The independent reviewer and TheoryDeveloper can continue
   through the existing outer AgentRuntime budget while the immutable finding
   ledger shows scientific progress. Runtime derives progress from prior
   findings marked resolved or retracted; merely adding a new finding while an
   old one remains unresolved is stagnation and stops before another theory
   model call. Revision count remains lineage telemetry, not a second budget.
7. Lean source workspaces now survive an exhausted inner tool-loop segment as
   one same-owner session. The checkpoint binds the immutable parent, exact
   current source, declaration, raw Lean diagnostic, latest RAG/proof-state
   observations, checked candidates, and observed-progress identities. The
   next outer step carries only a content-addressed observation reference; it
   does not regenerate a Formalizer packet or route through Architect. A
   tampered, stale, overlapping, or observation-free continuation stops before
   another provider call.
8. The independent theory referee now has the same durable-session semantics.
   When one inner segment ends after real document inspection, task-bound source
   retrieval, scratch execution, or terminal-validator feedback, AgentRuntime
   stores one content-addressed checkpoint and returns it to the same isolated
   reviewer in the next outer step. The checkpoint retains only exact
   model-visible observations, cumulative environment budgets, coverage refs,
   and immutable theory/material bindings; the task carries one
   `RuntimeArtifactRef`. It never copies author reasoning, asks Architect to
   replan, edits the referee report, or treats partial review work as acceptance.
   Tampering, a stale predecessor, repeated observations, or an observation-free
   segment stops before another reviewer call.
9. A TheoryDeveloper session reserves one control-plane terminal disposition
   after its unchanged environment-action budget. A final valid document write
   can therefore be followed by the same model's explicit checkpoint commit or
   gap report instead of being stranded by the tool-call counter. The reservation
   adds no research action, turn, retry, or runtime-authored stopping decision.
10. Executable scientific tasks freeze one compact, model-visible estimator ABI
    before the first model call. The same contract reaches the Theory, Python/R,
    Simulation, review, and Critic contexts, while schema-v2 hidden checks cite
    its stable public clauses and remain isolated after runtime termination.
    Agent outputs do not copy the full contract. This applies Codex's stable tool
    surface and exact observation-binding principle to scientific evaluation;
    it does not ask runtime to interpret statistics or repair model source.

These changes add no model call, retry, turn, agent, scheduler, model tier,
statistical formula, Lean grammar rule, or repair recipe.

### Live implication

The frozen jackknife-mean L0 draw provided a direct harness counterexample. Its
last successful theory write was valid and commit-ready, but the shared tool-call
counter reached zero while one provider turn remained. The next model-selected
terminal action was rejected before execution. Code commit `0d8a01e5` now keeps
one terminal disposition outside the unchanged research-action allowance.

This is the narrow Codex-style principle worth reusing: one same-session model
receives exact environment observations and remains responsible for ending its
own turn. AI-Statistician still retains `AgentRuntime` as the only outer
scientific scheduler and Claude as the required provider path. Codex thread,
app-server, Responses transport, and multi-agent persistence are not imported.
The consumed task remains `0/1`; deterministic regression cannot rescore it.

### Reused collaboration semantics

| AI-Statistician relation | Codex analogue | Required policy |
| --- | --- | --- |
| Same Theory/Python/R/Lean owner continues after raw feedback | another tool cycle or follow-up turn on one thread | retain the exact owner and workspace identity |
| Same owner resumes long mathematical work | resumed thread/follow-up task | load the hash-bound checkpoint and changed document ranges, not a copied semantic packet |
| Independent theory or code review | child with `fork_turns=none` | provide immutable artifact/source refs, never the author's hidden reasoning transcript |
| Algorithm or simulation consumes stable theory | queue-only message plus artifact | send a content-addressed ABI and claim refs; do not copy the full workspace |
| Simulation exposes a theory defect | follow-up task to the owning workspace | return the raw observation and bound artifact hashes; Architect is used only for a genuine ownership conflict |
| Optional Lean scout | isolated child over a stable theorem checkpoint | it may report formal status but cannot block non-formal evidence dimensions |
| Deep Lean proof | persistent source-owning coding thread | use goal, diagnostics, task-bound RAG, source edits, and kernel checks in one loop |

The independent reviewer and hidden evaluator must not adopt Codex's ordinary
shared-directory assumption. They require explicit visibility roots and
artifact-only inputs so author source, evaluator gold, and private results do
not become mutually visible.

## What is deliberately not imported

The current `openai_codex` Python SDK launches or connects to Codex app-server,
and the audited provider layer supports the Responses wire API. Directly using
it would replace the required Claude Haiku/Sonnet path or require a new
Anthropic-to-Responses proxy. It would also create a second scheduler and a
second persistence authority beside AgentRuntime.

Therefore this snapshot does not add:

- an `openai_codex` runtime dependency;
- an OpenAI model call or provider fallback;
- Codex thread state as a second scientific blackboard;
- shared author/reviewer/evaluator filesystem access;
- automatic subagent spawning for routine handoffs;
- a generic shell with access to evaluator-only artifacts.

The Rust sandbox, app-server, and MCP host remain future reuse candidates only
if they can be consumed behind the existing model-neutral tool executor and
visibility policy. They must replace measured local code, not wrap it.

## Next evidence gate

This adoption is a harness correction, not a capability result. It requires
deterministic regression proving that:

- declared model-actionable errors still return to the same model;
- an unexpected executor exception ends the loop before another model call and
  does not expose its message;
- multi-call turns retain call order and exact observation binding;
- Theory and Lean advertise multi-call turns while scientific source execution
  remains sequential;
- all frozen research outcomes remain unchanged.

No consumed benchmark may be rerun to claim that this mechanism works.

The visible-executable-contract correction has focused regression evidence only.
It validates stable public clauses, exact runtime and prompt propagation, legacy
question compatibility, evaluator identity binding, and fail-closed rejection of
unstated hidden-check semantics. Structural clause references remain provenance,
not proof that a hidden check is scientifically entailed; that preactivation
audit and independent harness calibration remain operator responsibilities. No
new live draw is authorized until the code is committed, the full suite passes,
and a future unrelated task is frozen under schema v2.

The deterministic continuation regression is complete at code commit
`9de34cf231b59f35985170775314834eeeebaf2d`: Algorithm and simulation both
resume with zero new planning calls and one same-owner source call; checkpoint
tampering and no-progress lineage are rejected. The focused workspace/runtime
panel passed 121 tests and the full local suite passed 769 tests. This is
mechanism evidence only: no model call, frozen-task rerun, scientific acceptance,
hidden-gold credit, or Lean proof credit was produced.

The theory-continuation correction is regression-validated at code commit
`fbc59a5fea8fca5bd99852d995ae68057ffddb83`. The redundant runtime config,
CLI flag, prompt budget, binding limit, and special reserved-revision exception
were deleted. A round-eight lineage that closes its prior finding continues to
round nine, while a lineage that closes none stops immediately. The affected
panel passed 229 tests and the full local suite passed 770 tests. No model call
or frozen-task rerun occurred, so this supplies no mathematical or E2E credit.

The Lean-continuation correction is regression-validated at code commit
`a1f47e08`. A two-segment source session restores the exact failed source,
compiler stderr, and formal-environment search result; the second segment does
not recheck or reinterpret the parent and retains its original parent hash.
Runtime continuation uses the same Formalizer and one hash-bound observation
reference, while content tampering and no-new-observation lineage fail closed.
The Lean/AgentRuntime panel passed 111 tests and the full local suite passed 773
tests in 72.97 seconds. No model call, benchmark rerun, theorem proof, hidden
evaluation, retry increase, turn increase, or new scheduling layer occurred.

The independent-referee continuation is regression-validated at code commit
`d64fd895`. A two-segment review restores the exact prior Markdown read, source
handle, and terminal-validator observation, then permits the same reviewer to
submit a complete review without rereading or regenerating its context. A real
`AgentRuntime` integration resolves the checkpoint through the blackboard,
calls the referee twice, and calls Architect planning zero times. Content
tampering and no-new-observation lineage fail before a provider call. The full
local suite passed 776 tests in 72.25 seconds. No live model call, frozen-task
rerun, retry or turn increase, mathematical acceptance, hidden-gold credit,
empirical credit, or proof credit was produced.
